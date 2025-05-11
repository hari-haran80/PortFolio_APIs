from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView


urlpatterns = [
    path('register/', RegisterUserAPIView.as_view(), name='register'),
    # path('verify-otp/', VerifyOTPAPIView.as_view(), name='verify-otp'),
    # path('resend-otp/', ResendOTPAPIView.as_view(), name='resend-otp'),  # Add this line
    path('login/', LoginAPIView.as_view(), name='login'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('delete-user/<int:pk>/', DeleteUserAPIView.as_view(), name='delete-user'),
    path('forgot-password/', ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('reset-password/<str:token>/', ResetPasswordAPIView.as_view(), name='reset-password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('health/', health_check, name='health-check'),

]