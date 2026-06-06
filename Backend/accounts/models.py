from django.db import models


class UserProfile(models.Model):
    """Профиль пользователя Telegram Mini-App. Это основа страницы 'Профиль'."""
    telegram_id = models.BigIntegerField('Telegram ID', unique=True)
    name = models.CharField('Имя', max_length=120)
    phone = models.CharField('Телефон', max_length=20, blank=True)

    # --- онбординг (проходится один раз) ---
    birth_year = models.PositiveIntegerField('Год рождения', null=True, blank=True)
    policy_accepted = models.BooleanField('Соглашение принято', default=False)
    survey_completed = models.BooleanField('Опрос пройден', default=False)

    balance = models.PositiveIntegerField('Баланс, ₽', default=0)
    invited_by = models.ForeignKey(
        'self', verbose_name='Кто пригласил', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='referrals'
    )
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)

    class Meta:
        verbose_name = 'Профиль'
        verbose_name_plural = 'Профили'

    def __str__(self):
        return f'{self.name} (#{self.telegram_id})'

    # --- статистика для страниц 'Профиль' и 'Главная' ---
    @property
    def codes_count(self):
        return self.code_entries.filter(status='accepted').count()

    @property
    def prizes_count(self):
        return self.user_prizes.count()

    @property
    def referrals_count(self):
        return self.referrals.count()
