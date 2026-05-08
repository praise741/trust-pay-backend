"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.views import APIView
from rest_framework.response import Response

class APIRootView(APIView):
    """API root endpoint"""
    def get(self, request):
        return Response({
            'message': 'Trust Pay API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth/',
                'deals': '/api/deals/',
                'admin': '/api/admin/',
                'webhooks': '/api/webhooks/',
                'merchant': '/api/merchant/',
                'buyer': '/api/buyer/',
            }
        })

urlpatterns = [
    path('', APIRootView.as_view(), name='api-root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('users.urls')),
    path('api/deals/', include('deals.urls')),
    path('api/admin/', include('deals.admin_api.urls')),
    path('api/webhooks/', include('payments.urls')),
    path('api/merchant/', include('deals.merchant.urls')),
    path('api/buyer/', include('deals.buyer.urls')),
    path('accounts/', include('allauth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
