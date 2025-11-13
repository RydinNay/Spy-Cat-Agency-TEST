from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SpyCatsViewSet

router = DefaultRouter()
router.register(r'spy-cats', SpyCatsViewSet, basename='spycat')

urlpatterns = [
    path('', include(router.urls)),
]