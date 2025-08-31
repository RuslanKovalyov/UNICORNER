from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import handler404


handler404 = 'main.views.p404'

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("main.urls")),
    path("qr-code-generator", include('qr_code.urls')),
    path("typing-test", include('typing_test.urls')),
    path("visual-translate", include('visualtranslate.urls')),
    path("warehouse/", include('warehouse.urls')),
    path("barista-ai/", include('barista_ai.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)