from django.db import models


class Prize(models.Model):
    """Приз, который разыгрывается (каталог призов)."""
    TYPE = [('combo', 'Комбо'), ('set', 'Сет'),
            ('cash', 'Денежный'), ('merch', 'Мерч')]
    title = models.CharField('Название', max_length=200)
    description = models.TextField('Описание')
    image_url = models.URLField('Картинка', blank=True)
    prize_type = models.CharField('Тип', max_length=10, choices=TYPE, default='merch')
    valid_until = models.DateField('Действует до', null=True, blank=True)
    is_main = models.BooleanField('Главный приз', default=False)

    class Meta:
        verbose_name = 'Приз'; verbose_name_plural = 'Призы'

    def __str__(self):
        return self.title


class UserPrize(models.Model):
    """Связь пользователя с призом (для статистики и вкладок)."""
    # 'purchased' убран: покупки — единый источник shop.Purchase, здесь только розыгрыш
    STATUS = [('won', 'Выигран'), ('pending', 'Ожидает')]
    user = models.ForeignKey('accounts.UserProfile', related_name='user_prizes',
                             on_delete=models.CASCADE)
    prize = models.ForeignKey(Prize, on_delete=models.CASCADE)
    status = models.CharField('Статус', max_length=10, choices=STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Приз пользователя'; verbose_name_plural = 'Призы пользователей'

    def __str__(self):
        return f'{self.user} — {self.prize} ({self.get_status_display()})'
