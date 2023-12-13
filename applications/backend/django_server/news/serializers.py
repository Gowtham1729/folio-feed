from rest_framework import serializers

from .models import Analysis, News, Ticker


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = "__all__"


class TickerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ticker
        fields = "__all__"


class AnalysisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analysis
        fields = "__all__"
