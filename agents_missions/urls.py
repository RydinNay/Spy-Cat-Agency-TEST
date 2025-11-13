from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SpyMissionViewSet

router = DefaultRouter()
router.register(r'spy-missions', SpyMissionViewSet, basename='spymission')

urlpatterns = [
    path('', include(router.urls)),
]
