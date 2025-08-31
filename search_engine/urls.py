from django.urls import path
from . import views

app_name = 'search_engine'

urlpatterns = [
    path('', views.search_view, name='search'),
]
