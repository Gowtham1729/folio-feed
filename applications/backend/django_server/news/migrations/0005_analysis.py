# Generated by Django 4.2.7 on 2023-12-11 12:52

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("news", "0004_alter_news_img_src_url_alter_news_src_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="Analysis",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("category", models.CharField(max_length=100)),
                ("symbol", models.CharField(max_length=100)),
                ("date", models.DateField()),
                ("average_sentiment", models.FloatField()),
                ("total_news", models.IntegerField()),
                ("positive_news", models.IntegerField()),
                ("negative_news", models.IntegerField()),
                ("need_attention", models.BooleanField()),
            ],
            options={
                "unique_together": {("symbol", "date")},
            },
        ),
    ]
