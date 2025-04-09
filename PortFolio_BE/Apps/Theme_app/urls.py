from django.urls import path
from . import views

urlpatterns = [
    path('api/theme/', views.get_theme, name='get-theme'),
    path('api/theme/set/', views.set_theme, name='set-theme'),
]