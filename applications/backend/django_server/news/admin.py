from django.contrib import admin

from .models import Analysis, News, Ticker

admin.site.register(News)
admin.site.register(Ticker)
admin.site.register(Analysis)
