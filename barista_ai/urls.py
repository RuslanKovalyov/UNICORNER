from django.urls import path
from . import views

app_name = 'barista_ai'

urlpatterns = [
    path('', views.barista_ai_interface, name='interface'),
]
