from django.db import models


class News(models.Model):
    category = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)

    src = models.CharField(max_length=2048)
    src_url = models.URLField(max_length=2048)
    img_src_url = models.URLField(max_length=2048)

    headline = models.TextField()
    summary = models.TextField()

    publish_time = models.DateTimeField()

    sentiment = models.IntegerField()

    class Meta:
        unique_together = ("symbol", "headline")

    def __str__(self):
        return self.headline


class Ticker(models.Model):
    ticker = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.ticker


class Analysis(models.Model):
    category = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)

    date = models.DateField()
    average_sentiment = models.FloatField()
    total_news = models.IntegerField()

    positive_news = models.IntegerField()
    negative_news = models.IntegerField()
    neutral_news = models.IntegerField()

    need_attention = models.BooleanField()

    class Meta:
        unique_together = ("symbol", "date")

    def __str__(self):
        return f"{self.symbol} - {self.date}"
