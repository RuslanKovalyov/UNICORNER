from django.urls import path
from .views import typing_test

urlpatterns = [
    path("", typing_test, name="typing_test"),
]
