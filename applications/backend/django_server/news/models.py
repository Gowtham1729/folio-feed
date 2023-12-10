from django.db import models


class News(models.Model):
    category = models.CharField(max_length=100)
    symbol = models.CharField(max_length=100)

    src = models.CharField(max_length=256)
    src_url = models.URLField(max_length=500)
    img_src_url = models.URLField(max_length=500)

    headline = models.TextField()
    summary = models.TextField()

    publish_time = models.DateTimeField()

    sentiment = models.CharField(max_length=100)

    class Meta:
        unique_together = ("symbol", "headline")

    def __str__(self):
        return self.headline


class Ticker(models.Model):
    ticker = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.ticker
