from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AboutMeViewSet, LanguageViewSet, ExperienceViewSet, EducationViewSet

router = DefaultRouter()
router.register('about-me', AboutMeViewSet)
router.register('languages', LanguageViewSet)
router.register('experience', ExperienceViewSet)
router.register('education', EducationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
