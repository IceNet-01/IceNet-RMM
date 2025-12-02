"""
URL routing for agents app
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    OrganizationViewSet,
    AgentViewSet,
    AgentCommandViewSet,
    AgentMetricViewSet,
    InstalledSoftwareViewSet,
    AgentLogViewSet
)

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'', AgentViewSet, basename='agent')
router.register(r'commands', AgentCommandViewSet, basename='command')
router.register(r'metrics', AgentMetricViewSet, basename='metric')
router.register(r'software', InstalledSoftwareViewSet, basename='software')
router.register(r'logs', AgentLogViewSet, basename='log')

urlpatterns = [
    path('', include(router.urls)),
]
