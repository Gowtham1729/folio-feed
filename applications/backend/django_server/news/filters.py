import django_filters

from .models import News


class NewsFilter(django_filters.FilterSet):
    date = django_filters.DateFilter(field_name="publish_time", lookup_expr="date")

    class Meta:
        model = News
        fields = ["category", "symbol", "src", "need_attention", "date"]
