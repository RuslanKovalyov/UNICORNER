from django.urls import path
from .views import visualtranslate

urlpatterns = [
    path("", visualtranslate, name="visual_translate"),
]
