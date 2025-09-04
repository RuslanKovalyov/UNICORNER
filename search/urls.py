from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.search_view, name='search'),
    path('dashboard/', views.crawler_dashboard, name='crawler_dashboard'),
    path('api/crawler/', views.crawler_api, name='crawler_api'),
]
