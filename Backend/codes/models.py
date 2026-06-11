from django.db import models


class PromoCode(models.Model):
    """Пул валидных кодов под крышками. Каждый код активируется ОДИН раз."""
    code = models.CharField('Код', max_length=40, unique=True)
    reward = models.PositiveIntegerField('Награда, ₽', default=10)
    is_active = models.BooleanField('Активен', default=True)
    redeemed_by = models.ForeignKey(
        'accounts.UserProfile', verbose_name='Активировал',
        null=True, blank=True, on_delete=models.SET_NULL, related_name='redeemed_codes'
    )
    redeemed_at = models.DateTimeField('Когда активирован', null=True, blank=True)

    class Meta:
        verbose_name = 'Промокод'; verbose_name_plural = 'Промокоды'

    def __str__(self):
        return self.code


class CodeEntry(models.Model):
    """История ввода кодов пользователем (страница 'Коды')."""
    STATUS = [
        ('accepted', 'Принят'),
        ('lose',     'Не выигрыш'),
        ('invalid',  'Неверный'),
        ('used',     'Уже использован'),
    ]
    user = models.ForeignKey('accounts.UserProfile', related_name='code_entries',
                             on_delete=models.CASCADE)
    code_text = models.CharField('Введённый код', max_length=40)
    status = models.CharField('Статус', max_length=10, choices=STATUS)
    reward = models.PositiveIntegerField('Начислено, ₽', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Запись кода'; verbose_name_plural = 'История кодов'

    def __str__(self):
        return f'{self.code_text} — {self.get_status_display()}'
