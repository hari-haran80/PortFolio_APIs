from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SkillViewSet, SkillCategoryViewSet

router = DefaultRouter()
router.register(r'skills', SkillViewSet)
router.register(r'skill-categories', SkillCategoryViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
