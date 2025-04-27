from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AboutMeViewSet, LanguageViewSet, ExperienceViewSet, EducationViewSet, total_commits

router = DefaultRouter()
router.register('about-me', AboutMeViewSet)
router.register('languages', LanguageViewSet)
router.register('experience', ExperienceViewSet)
router.register('education', EducationViewSet)

urlpatterns = [
    path('', include(router.urls)),    
    path('total-commits/', total_commits, name='total-commits'),
]
