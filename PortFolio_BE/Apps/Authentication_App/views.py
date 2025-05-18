from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from .serializers import *
from .models import *
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from django.contrib.auth import update_session_auth_hash
from Apps.Profile_App.models import Profile
from django.utils.crypto import get_random_string
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from Apps.Theme_app.serializers import UserThemeSerializer
from Apps.Theme_app.models import UserTheme
from rest_framework.decorators import api_view, permission_classes

User = get_user_model()

class RegisterUserAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user_data = serializer.validated_data

            # Create the user
            user = User.objects.create_user(
                username=user_data['username'],
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                email=user_data['email'],
                password=user_data.get('password', 'defaultpassword')
            )

            # Create Profile if not exists
            Profile.objects.get_or_create(
                user=user,
                defaults={
                    'profile_picture': None,
                    'gender': 'O',
                    'position': 'Employee',
                    'phone_number': '+1234567890'
                }
            )

            # Send email notification
            send_mail(
                'New User Registration',
                f'A new user has registered: {user.username}',
                settings.EMAIL_HOST_USER,
                [settings.ADMIN_EMAIL],
                fail_silently=False,
            )

            return Response({'message': 'Account created successfully.'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        
class LoginAPIView(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)

            # Safer query - prevents MultipleObjectsReturned
            theme = UserTheme.objects.filter(user=user).first()  # If user-specific
            # theme = UserTheme.objects.first()  # If global

            theme_data = UserThemeSerializer(theme).data if theme else {}

            return Response({
                'user_id': user.id,
                'is_superuser': user.is_superuser,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'theme': theme_data,
            }, status=status.HTTP_200_OK)

        return Response({'message': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class LogoutAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logout successful'}, status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        

        
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'error': 'Wrong old password'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        return Response({'message': 'Password updated successfully'}, status=status.HTTP_200_OK)




class DeleteUserAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can delete their account

    def delete(self, request, pk):
        try:
            # Retrieve the user to be deleted
            user = User.objects.get(pk=pk)

            # Ensure the user can only delete their own account
            if user != request.user and not request.user.is_superuser:
                return Response(
                    {"message": "You do not have permission to delete this user."},
                        status=status.HTTP_403_FORBIDDEN
                    )

            # Delete the user (this will also delete the associated Profile due to on_delete=CASCADE)
            user.delete()

            return Response(
                {"message": "User deleted successfully."},
                status=status.HTTP_204_NO_CONTENT
            )

        except User.DoesNotExist:
            return Response(
                {"message": "User not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
class ForgotPasswordAPIView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email=email).first()

            if user:
                # Generate a unique token
                token = get_random_string(length=32)
                # Save the token in the database
                PasswordResetToken.objects.create(user=user, token=token)

                # Send email with reset link
                reset_link = f"{settings.FRONTEND_URL}/reset-password/{token}/"
                send_mail(
                    'Password Reset Request',
                    f'Click the link to reset your password: {reset_link}',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False,
                )

                return Response({'success': 'Password reset link sent to your email.', 'token': token}, status=status.HTTP_200_OK)
            return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ResetPasswordAPIView(APIView):
    permission_classes = []

    def post(self, request, token):
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        if new_password != confirm_password:
            return Response({'message': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

        reset_token = PasswordResetToken.objects.filter(token=token).first()

        if reset_token:
            user = reset_token.user
            user.set_password(new_password)
            user.save()
            reset_token.delete()  # Delete the token after use
            return Response({'message': 'Password reset successfully.'}, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid or expired token.'}, status=status.HTTP_400_BAD_REQUEST)
    


def health_check(request):
    return JsonResponse({"status": "ok"}, status=200)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_token(request):
    return Response({"message": "Token is valid"}, status=200)
