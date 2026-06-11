from rest_framework import serializers
from .models import Prize, UserPrize


class PrizeSerializer(serializers.ModelSerializer):
    type_display = serializers.CharField(source='get_prize_type_display', read_only=True)

    class Meta:
        model = Prize
        fields = ['id', 'title', 'description', 'image_url',
                  'prize_type', 'type_display', 'valid_until', 'is_main', 'win_chance']


class UserPrizeSerializer(serializers.ModelSerializer):
    prize = PrizeSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = UserPrize
        fields = ['id', 'prize', 'status', 'status_display', 'created_at']
