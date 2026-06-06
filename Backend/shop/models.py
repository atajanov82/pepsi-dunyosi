from django.db import models


class Product(models.Model):
    """Товар в магазине, покупается за рубли (баланс пользователя)."""
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    image_url = models.URLField('Картинка', blank=True)
    price = models.PositiveIntegerField('Цена, ₽')
    stock = models.PositiveIntegerField('Остаток', default=0)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Товар'; verbose_name_plural = 'Товары'

    def __str__(self):
        return f'{self.name} — {self.price}₽'


class Purchase(models.Model):
    """Покупка/заказ товара пользователем (с этапом доставки)."""
    STATUS = [
        ('assembling', 'Собирается'),
        ('shipping',   'В пути'),
        ('arrived',    'Приехал'),
        ('handed',     'Выдан покупателю'),
        ('cancelled',  'Отменён'),
    ]
    user = models.ForeignKey('accounts.UserProfile', related_name='purchases',
                             on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price_paid = models.PositiveIntegerField('Оплачено, ₽')
    status = models.CharField('Статус заказа', max_length=12,
                              choices=STATUS, default='assembling')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Заказ'; verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.user} купил {self.product} ({self.get_status_display()})'
