import re
from datetime import date
from rest_framework import serializers
from .models import UserProfile

PHONE_RE = re.compile(r'^\+?\d[\d\s\-()]{6,18}\d$')


class RegisterSerializer(serializers.ModelSerializer):
    """Регистрация: создаём профиль (один раз).
    Необязательное поле ref — telegram_id пригласившего (реферальная ссылка)."""
    ref = serializers.IntegerField(required=False, allow_null=True, write_only=True)
    # без UniqueValidator (идемпотентность через get_or_create) и необязательно:
    # в проде telegram_id берётся из проверенного initData, а не из тела
    telegram_id = serializers.IntegerField(required=False)

    class Meta:
        model = UserProfile
        fields = ['telegram_id', 'name', 'phone', 'ref']

    def validate_phone(self, value):
        value = (value or '').strip()
        if value and not PHONE_RE.match(value):
            raise serializers.ValidationError('Некорректный номер телефона')
        return value


class ProfileSerializer(serializers.ModelSerializer):
    """Данные для страницы 'Профиль' + 'Моя статистика'."""
    codes_count = serializers.IntegerField(read_only=True)
    prizes_count = serializers.IntegerField(read_only=True)
    referrals_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = UserProfile
        fields = ['id', 'telegram_id', 'name', 'phone', 'balance',
                  'birth_year', 'policy_accepted', 'survey_completed',
                  'codes_count', 'prizes_count', 'referrals_count', 'created_at']


class PolicySerializer(serializers.Serializer):
    """Принятие соглашения (шаг онбординга)."""
    accepted = serializers.BooleanField()


class BirthYearSerializer(serializers.Serializer):
    """Год рождения (возрастная проверка, спрашивается один раз)."""
    birth_year = serializers.IntegerField(min_value=1900)

    def validate_birth_year(self, value):
        cur = date.today().year
        if value > cur:
            raise serializers.ValidationError('Год рождения не может быть в будущем')
        return value
