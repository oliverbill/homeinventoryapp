
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve

from homeinventoryapp import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("homeinventoryapi.urls")),
    path("api-auth/", include("rest_framework.urls")),
]
