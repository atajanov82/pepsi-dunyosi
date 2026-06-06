from rest_framework import serializers
from .models import CodeEntry


class SubmitCodeSerializer(serializers.Serializer):
    """Ввод кода с главной страницы."""
    code = serializers.CharField(max_length=40)


class CodeEntrySerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = CodeEntry
        fields = ['id', 'code_text', 'status', 'status_display', 'reward', 'created_at']
