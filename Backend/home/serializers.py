from rest_framework import serializers
from .models import Banner, Raffle, SurveyQuestion, SurveyOption


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['id', 'title', 'image_url']


class RaffleWinSerializer(serializers.Serializer):
    code_text = serializers.CharField()
    prize_title = serializers.CharField(source='prize.title')
    winner_name = serializers.CharField(source='user.name')


class RaffleSerializer(serializers.ModelSerializer):
    is_done = serializers.BooleanField(read_only=True)
    wins = RaffleWinSerializer(many=True, read_only=True)
    winners_count = serializers.SerializerMethodField()

    class Meta:
        model = Raffle
        fields = ['id', 'title', 'draw_at', 'recording_url',
                  'is_done', 'drawn_at', 'winners_count', 'wins']

    def get_winners_count(self, obj):
        return obj.wins.count()


class SurveyOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyOption
        fields = ['id', 'text']


class SurveyQuestionSerializer(serializers.ModelSerializer):
    options = SurveyOptionSerializer(many=True, read_only=True)

    class Meta:
        model = SurveyQuestion
        fields = ['id', 'text', 'options']


class SurveyAnswerInputSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    option = serializers.IntegerField()


class SubmitSurveySerializer(serializers.Serializer):
    """Отправка ответов опроса: список {question, option}."""
    answers = SurveyAnswerInputSerializer(many=True, allow_empty=False)
