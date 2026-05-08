from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, SellerProfileView, PublicSellerProfileView
from .google_auth import google_login

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),
    path('google/', google_login, name='google-login'),
    path('profile/', SellerProfileView.as_view(), name='seller-profile'),
    path('sellers/<str:username>/', PublicSellerProfileView.as_view(), name='public-seller-profile'),
]
