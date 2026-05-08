from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.BuyerDashboardView.as_view(), name='buyer-dashboard'),
    path('orders/<slug:slug>/', views.BuyerOrderDetailView.as_view(), name='buyer-order-detail'),
    path('orders/<slug:slug>/tracking/', views.BuyerOrderTrackingView.as_view(), name='buyer-order-tracking'),
    path('orders-by-phone/', views.BuyerOrdersByPhoneView.as_view(), name='buyer-orders-by-phone'),
]
