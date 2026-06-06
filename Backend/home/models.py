from django.db import models


class Banner(models.Model):
    """Слайды карусели на главной."""
    title = models.CharField('Заголовок', max_length=120, blank=True)
    image_url = models.URLField('Картинка')
    order = models.PositiveIntegerField('Порядок', default=0)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Баннер'; verbose_name_plural = 'Баннеры'

    def __str__(self):
        return self.title or f'Баннер #{self.id}'


class Raffle(models.Model):
    """Розыгрыш — для блока 'До розыгрыша осталось' (таймер)."""
    title = models.CharField('Название', max_length=200)
    draw_at = models.DateTimeField('Дата и время розыгрыша')
    recording_url = models.URLField('Запись розыгрыша', blank=True)
    is_active = models.BooleanField('Активен', default=True)

    class Meta:
        verbose_name = 'Розыгрыш'; verbose_name_plural = 'Розыгрыши'

    def __str__(self):
        return self.title


class SurveyQuestion(models.Model):
    """Вопрос опроса. За весь опрос начисляется 250 ₽ (один раз)."""
    text = models.CharField('Вопрос', max_length=300)
    order = models.PositiveIntegerField('Порядок', default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Вопрос опроса'; verbose_name_plural = 'Вопросы опроса'

    def __str__(self):
        return self.text


class SurveyOption(models.Model):
    """Вариант ответа на вопрос опроса."""
    question = models.ForeignKey(SurveyQuestion, related_name='options',
                                 on_delete=models.CASCADE)
    text = models.CharField('Вариант', max_length=200)

    def __str__(self):
        return self.text


class SurveyAnswer(models.Model):
    """Ответ пользователя на вопрос опроса (раньше ответы не сохранялись)."""
    user = models.ForeignKey('accounts.UserProfile', related_name='survey_answers',
                             on_delete=models.CASCADE)
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE)
    option = models.ForeignKey(SurveyOption, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'question')  # один ответ на вопрос
        verbose_name = 'Ответ опроса'; verbose_name_plural = 'Ответы опроса'

    def __str__(self):
        return f'{self.user} — {self.question_id}: {self.option_id}'
