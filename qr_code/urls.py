from django.urls import path
from .views import generate_qr_code

urlpatterns = [
    path("qr-code-generator", generate_qr_code, name="generate_qr_code"),
]
