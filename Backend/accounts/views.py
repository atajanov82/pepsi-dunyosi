from datetime import date
from django.conf import settings
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile
from .serializers import (RegisterSerializer, ProfileSerializer,
                          PolicySerializer, BirthYearSerializer)
from .utils import get_user, resolve_telegram_id
from .telegram import parse_init_data


class WhoAmIView(APIView):
    """GET /api/accounts/whoami/ — диагностика авторизации (без секретов).
    Помогает безопасно проверить, приходит ли валидный initData, ДО включения строгого режима."""
    def get(self, request):
        init_data = request.headers.get('X-Telegram-Init-Data')
        valid = False
        tid = None
        if init_data and settings.TELEGRAM_BOT_TOKEN:
            u = parse_init_data(init_data, settings.TELEGRAM_BOT_TOKEN,
                                settings.TELEGRAM_INITDATA_MAX_AGE)
            if u and u.get('id'):
                valid, tid = True, u['id']
        if valid:
            method = 'initData'
        elif settings.TELEGRAM_ALLOW_INSECURE and (
                request.data.get('telegram_id') or request.query_params.get('telegram_id')):
            method = 'insecure'
        else:
            method = 'none'
        return Response({
            'method': method,
            'has_init_data': bool(init_data),
            'init_data_valid': valid,
            'token_set': bool(settings.TELEGRAM_BOT_TOKEN),
            'insecure_mode': settings.TELEGRAM_ALLOW_INSECURE,
            'telegram_id': tid,
        })


class RegisterView(APIView):
    """POST /api/accounts/register/  — регистрация (один раз).
    Принимает необязательный ref (telegram_id пригласившего) — реферальная программа."""
    throttle_scope = 'register'   # анти-спам / анти-фрод рефералов

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = dict(s.validated_data)
        ref = data.pop('ref', None)

        # настоящий telegram_id — из проверенного initData (прод), иначе из тела (dev)
        resolved = resolve_telegram_id(request) or data.get('telegram_id')
        try:
            data['telegram_id'] = int(resolved)
        except (TypeError, ValueError):
            return Response({'detail': 'Нужен корректный telegram_id'},
                            status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            profile, created = UserProfile.objects.get_or_create(
                telegram_id=data['telegram_id'],
                defaults=data,
            )
            # Реферал: начисляем награду пригласившему один раз — при создании нового профиля
            if created and ref and ref != profile.telegram_id and profile.invited_by_id is None:
                inviter = (UserProfile.objects
                           .select_for_update()
                           .filter(telegram_id=ref)
                           .first())
                if inviter:
                    profile.invited_by = inviter
                    profile.save(update_fields=['invited_by'])
                    inviter.balance += settings.REFERRAL_REWARD
                    inviter.save(update_fields=['balance'])

        return Response(
            {'created': created, 'profile': ProfileSerializer(profile).data},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ProfileView(APIView):
    """GET /api/accounts/profile/?telegram_id=... — данные профиля + статистика."""
    def get(self, request):
        profile = get_user(request)
        return Response(ProfileSerializer(profile).data)


class OnboardingStatusView(APIView):
    """GET /api/accounts/onboarding/?telegram_id=... — какой шаг онбординга показать.
    Если пользователь ещё не зарегистрирован — отдаём шаг 'register' без ошибки."""
    def get(self, request):
        tg = request.query_params.get('telegram_id')
        try:
            tg = int(tg) if tg else None
        except (TypeError, ValueError):
            tg = None
        profile = UserProfile.objects.filter(telegram_id=tg).first() if tg else None
        if profile is None:
            return Response({'registered': False, 'policy_accepted': False,
                             'birth_year_set': False, 'survey_completed': False,
                             'next_step': 'register'})
        if not profile.policy_accepted:
            next_step = 'policy'
        elif not profile.birth_year:
            next_step = 'birth_year'
        else:
            next_step = 'done'
        return Response({
            'registered': True,
            'policy_accepted': profile.policy_accepted,
            'birth_year_set': bool(profile.birth_year),
            'survey_completed': profile.survey_completed,
            'next_step': next_step,
        })


class AcceptPolicyView(APIView):
    """POST /api/accounts/policy/ — принять соглашение (шаг онбординга)."""
    def post(self, request):
        profile = get_user(request)
        s = PolicySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        profile.policy_accepted = s.validated_data['accepted']
        profile.save(update_fields=['policy_accepted'])
        return Response({'policy_accepted': profile.policy_accepted})


class BirthYearView(APIView):
    """POST /api/accounts/birth-year/ — указать год рождения (один раз)."""
    def post(self, request):
        profile = get_user(request)
        if profile.birth_year:
            return Response({'detail': 'Год рождения уже указан'},
                            status=status.HTTP_400_BAD_REQUEST)
        s = BirthYearSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        year = s.validated_data['birth_year']
        age = date.today().year - year
        if age < settings.MIN_AGE:
            return Response({'detail': f'Участие с {settings.MIN_AGE} лет'},
                            status=status.HTTP_403_FORBIDDEN)
        profile.birth_year = year
        profile.save(update_fields=['birth_year'])
        return Response({'birth_year': year, 'age': age})
