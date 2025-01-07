from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name='home'),
    path('contacts', views.contacts, name='contacts'),
    path('about', views.about, name='about'),
    path('terms_and_privacy', views.terms_and_privacy, name='terms_and_privacy'),
]