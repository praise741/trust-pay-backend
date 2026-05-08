from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, SellerProfileView, PublicSellerProfileView, CustomTokenObtainPairView
from .google_auth import google_login, google_config_check

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('google/', google_login, name='google-login'),
    path('google/config/', google_config_check, name='google-config-check'),
    path('profile/', SellerProfileView.as_view(), name='seller-profile'),
    path('sellers/<str:username>/', PublicSellerProfileView.as_view(), name='public-seller-profile'),
]
