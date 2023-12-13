from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"news", views.NewsViewSet)
router.register(r"tickers", views.TickerViewSet)
router.register(r"analysis", views.AnalysisViewSet)

urlpatterns = [
    # path("", views.index, name="main_index"),
    path("api/", include(router.urls)),
    path("home", views.home, name="home"),
    path("news/<str:symbol>/<str:date>", views.news, name="news"),
]
