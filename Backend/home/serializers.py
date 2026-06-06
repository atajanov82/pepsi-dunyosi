from rest_framework import serializers
from .models import Banner, Raffle, SurveyQuestion, SurveyOption


class BannerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banner
        fields = ['id', 'title', 'image_url']


class RaffleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Raffle
        fields = ['id', 'title', 'draw_at', 'recording_url']


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
