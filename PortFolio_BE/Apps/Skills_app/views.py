from rest_framework import viewsets
from Apps.Authentication_App.permissions import IsAdminOrReadOnly
from .models import Skill, SkillCategory
from .serializers import SkillSerializer, SkillCategorySerializer


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.select_related("category").order_by("id")
    serializer_class = SkillSerializer
    permission_classes = [IsAdminOrReadOnly]


class SkillCategoryViewSet(viewsets.ModelViewSet):
    queryset = SkillCategory.objects.prefetch_related("skills").order_by("id")
    serializer_class = SkillCategorySerializer
    permission_classes = [IsAdminOrReadOnly]
