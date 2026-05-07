from django.urls import path
from . import views

urlpatterns = [
    path('payaza/', views.payaza_webhook, name='payaza-webhook'),
]
