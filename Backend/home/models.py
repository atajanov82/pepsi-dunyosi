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
    """Розыгрыш на дату: рулетка случайно выбирает выигрышный код среди введённых."""
    title = models.CharField('Название', max_length=200)
    draw_at = models.DateTimeField('Дата и время розыгрыша')
    recording_url = models.URLField('Запись розыгрыша', blank=True)
    is_active = models.BooleanField('Активен', default=True)

    # результат розыгрыша (заполняется при проведении)
    winner = models.ForeignKey('accounts.UserProfile', verbose_name='Победитель',
                               null=True, blank=True, on_delete=models.SET_NULL,
                               related_name='won_raffles')
    winning_code = models.CharField('Выигравший код', max_length=40, blank=True)
    drawn_at = models.DateTimeField('Когда проведён', null=True, blank=True)

    class Meta:
        ordering = ['draw_at']
        verbose_name = 'Розыгрыш'; verbose_name_plural = 'Розыгрыши'

    def __str__(self):
        return self.title

    @property
    def is_done(self):
        return self.drawn_at is not None


class RaffleWin(models.Model):
    """Один выигрыш в розыгрыше: код -> приз -> пользователь (победителей может быть много)."""
    raffle = models.ForeignKey(Raffle, related_name='wins', on_delete=models.CASCADE)
    user = models.ForeignKey('accounts.UserProfile', related_name='raffle_wins',
                             on_delete=models.CASCADE)
    prize = models.ForeignKey('prizes.Prize', on_delete=models.CASCADE)
    code_text = models.CharField('Выигравший код', max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Выигрыш розыгрыша'; verbose_name_plural = 'Выигрыши розыгрышей'

    def __str__(self):
        return f'{self.code_text} -> {self.prize} ({self.user})'


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
