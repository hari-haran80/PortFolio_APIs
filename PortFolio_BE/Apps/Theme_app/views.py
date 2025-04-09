from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserTheme
from .serializers import UserThemeSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_theme(request):
    user_theme, created = UserTheme.objects.get_or_create(user=request.user)
    serializer = UserThemeSerializer(user_theme)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_theme(request):
    user_theme, created = UserTheme.objects.get_or_create(user=request.user)
    serializer = UserThemeSerializer(user_theme, data=request.data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)