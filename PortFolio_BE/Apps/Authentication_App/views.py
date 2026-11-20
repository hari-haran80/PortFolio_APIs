import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.utils.crypto import get_random_string
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from Apps.Theme_app.models import UserTheme
from Apps.Theme_app.serializers import UserThemeSerializer
from .models import PasswordResetToken
from .serializers import ForgotPasswordSerializer, UserRegistrationSerializer

logger = logging.getLogger(__name__)
User = get_user_model()


def _password_errors(password, user=None):
    """Run Django's password validators and return a list of messages (empty if valid)."""
    if not password:
        return ["Password is required."]
    try:
        validate_password(password, user=user)
    except DjangoValidationError as exc:
        return list(exc.messages)
    return []


class AuthThrottleMixin:
    """Rate-limit unauthenticated auth endpoints against brute force / spam."""
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RegisterUserAPIView(AuthThrottleMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = User.objects.create_user(
            username=data['username'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            email=data['email'],
            password=data['password'],
        )

        try:
            send_mail(
                'New User Registration',
                f'A new user has registered: {user.username}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )
        except Exception:
            # The account exists; a mail outage must not report registration as failed.
            logger.exception("Failed to send new-registration notification")

        return Response({'message': 'Account created successfully.'}, status=status.HTTP_201_CREATED)


class LoginAPIView(AuthThrottleMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'message': 'Username and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        refresh = RefreshToken.for_user(user)
        theme = UserTheme.objects.filter(user=user).first()

        return Response({
            'user_id': user.id,
            'is_superuser': user.is_superuser,
            'last_login': user.last_login,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'theme': UserThemeSerializer(theme).data if theme else {},
        }, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'message': 'Refresh token is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            RefreshToken(refresh_token).blacklist()
        except Exception:
            return Response({'message': 'Invalid or expired refresh token.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': 'Logout successful'}, status=status.HTTP_205_RESET_CONTENT)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not user.check_password(old_password):
            return Response(
                {'message': 'Wrong old password', 'error': 'Wrong old password'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        errors = _password_errors(new_password, user)
        if errors:
            msg = " ".join(errors)
            return Response({'message': msg, 'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)


class DeleteUserAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        user = User.objects.filter(pk=pk).first()
        if not user:
            return Response({"message": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user != request.user and not request.user.is_superuser:
            return Response(
                {"message": "You do not have permission to delete this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ForgotPasswordAPIView(AuthThrottleMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    # Same answer whether or not the email exists, so the endpoint can't be used
    # to discover which emails have accounts.
    GENERIC_RESPONSE = {'success': 'If an account exists for this email, a password reset link has been sent.'}

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            # Only the newest link is valid.
            PasswordResetToken.objects.filter(user=user).delete()
            token = get_random_string(length=32)
            PasswordResetToken.objects.create(user=user, token=token)

            reset_link = f"{settings.FRONTEND_URL}/reset-password/{token}"
            ttl = settings.PASSWORD_RESET_TOKEN_TTL_MINUTES
            try:
                send_mail(
                    'Password Reset Request',
                    f'Click the link to reset your password (valid for {ttl} minutes): {reset_link}\n\n'
                    'If you did not request this, you can ignore this email.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except Exception:
                logger.exception("Failed to send password reset email")
                return Response(
                    {'error': 'Could not send the reset email right now. Please try again later.'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

        return Response(self.GENERIC_RESPONSE, status=status.HTTP_200_OK)


class ResetPasswordAPIView(AuthThrottleMixin, APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, token):
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if new_password != confirm_password:
            return Response({'message': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        reset_token = PasswordResetToken.objects.select_related('user').filter(token=token).first()
        expiry = timedelta(minutes=settings.PASSWORD_RESET_TOKEN_TTL_MINUTES)
        if not reset_token or reset_token.created_at < timezone.now() - expiry:
            if reset_token:
                reset_token.delete()
            return Response({'message': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)

        user = reset_token.user
        errors = _password_errors(new_password, user)
        if errors:
            return Response({'message': " ".join(errors)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        PasswordResetToken.objects.filter(user=user).delete()
        return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)


def health_check(request):
    return JsonResponse({"status": "ok"}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    return Response({"message": "Token is valid"}, status=200)
