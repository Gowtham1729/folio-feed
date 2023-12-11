from django.contrib import admin

from .models import News, Ticker, Analysis

admin.site.register(News)
admin.site.register(Ticker)
admin.site.register(Analysis)
