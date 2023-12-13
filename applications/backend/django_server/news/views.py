from django.utils import timezone

from rest_framework import viewsets

from .models import Analysis, News, Ticker
from .serializers import AnalysisSerializer, NewsSerializer, TickerSerializer


class NewsViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = News.objects.all()
    serializer_class = NewsSerializer

    def get_queryset(self):
        queryset = News.objects.all()
        category = self.request.query_params.get("category")
        symbol = self.request.query_params.get("symbol")
        src = self.request.query_params.get("src")
        need_attention = self.request.query_params.get("need_attention")
        date_param = self.request.query_params.get("date")
        if category:
            queryset = queryset.filter(category=category)
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        if src:
            queryset = queryset.filter(src=src)
        if need_attention:
            queryset = queryset.filter(need_attention=need_attention)
        if date_param:
            try:
                date = timezone.datetime.strptime(date_param, "%Y-%m-%d").date()
                queryset = queryset.filter(publish_time__date=date)
            except ValueError:
                pass
        return queryset


class TickerViewSet(viewsets.ModelViewSet):
    queryset = Ticker.objects.all()
    serializer_class = TickerSerializer


class AnalysisViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Analysis.objects.all()
    serializer_class = AnalysisSerializer

    def get_queryset(self):
        queryset = Analysis.objects.all()
        category = self.request.query_params.get("category")
        symbol = self.request.query_params.get("symbol")
        need_attention = self.request.query_params.get("need_attention")
        date_param = self.request.query_params.get("date")
        if category:
            queryset = queryset.filter(category=category)
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        if need_attention:
            queryset = queryset.filter(need_attention=need_attention)
        if date_param:
            try:
                date = timezone.datetime.strptime(date_param, "%Y-%m-%d").date()
                queryset = queryset.filter(date=date)
            except ValueError:
                pass
        return queryset
