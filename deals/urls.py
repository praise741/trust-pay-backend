from django.urls import path
from . import views

urlpatterns = [
    path('', views.DealListCreateView.as_view(), name='deal-list-create'),
    path('<slug:slug>/', views.DealDetailView.as_view(), name='deal-detail'),
    path('<slug:slug>/pay/', views.deal_pay, name='deal-pay'),
    path('<slug:slug>/ship/', views.deal_ship, name='deal-ship'),
    path('<slug:slug>/tracking/', views.update_tracking, name='update-tracking'),
    path('<slug:slug>/confirm/', views.deal_confirm, name='deal-confirm'),
    path('<slug:slug>/dispute/', views.deal_dispute, name='deal-dispute'),
    path('<slug:slug>/mock-pay/', views.deal_mock_pay, name='deal-mock-pay'),
]
