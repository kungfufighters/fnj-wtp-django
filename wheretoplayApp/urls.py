from django.urls import path, include
from .views import *

urlpatterns = [
    path('health/', HealthView.as_view(), name='health'),
]

