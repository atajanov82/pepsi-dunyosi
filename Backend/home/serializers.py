from rest_framework import serializers
from .models import Banner, Raffle, SurveyQuestion, SurveyOption


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['id', 'title', 'image_url']


class RaffleSerializer(serializers.ModelSerializer):
    is_done = serializers.BooleanField(read_only=True)
    winner_name = serializers.SerializerMethodField()

    class Meta:
        model = Raffle
        fields = ['id', 'title', 'draw_at', 'recording_url',
                  'is_done', 'winning_code', 'drawn_at', 'winner_name']

    def get_winner_name(self, obj):
        return obj.winner.name if obj.winner_id else ''


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
