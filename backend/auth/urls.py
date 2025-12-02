"""
URL routing for auth app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

router = DefaultRouter()
router.register(r'audit-logs', views.AuditLogViewSet, basename='audit-log')

urlpatterns = [
    # JWT tokens
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # MFA
    path('mfa/setup/', views.setup_mfa, name='mfa_setup'),
    path('mfa/verify/', views.verify_mfa, name='mfa_verify'),
    path('mfa/disable/', views.disable_mfa, name='mfa_disable'),

    # Router URLs
    path('', include(router.urls)),
]
