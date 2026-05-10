"""
Authentication API views.

Provides REST API endpoints for user registration, login, logout,
and retrieving the current authenticated user's profile information.
Uses JWT token-based authentication via Django REST Framework SimpleJWT.
"""

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer, UserSerializer


class RegisterView(APIView):
    """API endpoint for user registration.

    Accepts registration data, validates it, creates a new user account,
    and returns the created user along with JWT access and refresh tokens.
    This endpoint is publicly accessible without authentication.

    Attributes:
        permission_classes: Allows unrestricted access for new user registration.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Handle user registration request.

        Validates the registration data, creates the user account,
        generates JWT tokens, and returns the response.

        Args:
            request: HTTP request containing registration data with fields
                including email, password, password_confirm, first_name,
                and last_name.

        Returns:
            Response: HTTP 201 with user data and JWT tokens on success,
                or HTTP 400 with validation errors on failure.
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate JWT tokens for the newly registered user
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """API endpoint for user logout.

    Invalidates the user's refresh token by adding it to the token
    blacklist, preventing future token refresh operations.
    """

    def post(self, request):
        """Handle user logout request.

        Extracts the refresh token from the request data, validates it,
        and adds it to the blacklist to prevent further use.

        Args:
            request: HTTP request containing a 'refresh' field with the
                JWT refresh token to be invalidated.

        Returns:
            Response: HTTP 200 with a success message on successful logout,
                or HTTP 400 with an error message if the token is invalid.
        """
        try:
            # Extract refresh token from request body
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            # Add token to blacklist to prevent reuse
            token.blacklist()
            return Response({'detail': 'Logout effettuato.'}, status=status.HTTP_200_OK)
        except TokenError:
            # Catch invalid, expired, or malformed tokens
            return Response(
                {'error': 'Token non valido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    """API endpoint for retrieving the current authenticated user's profile.

    Requires authentication. Returns the profile information of the
    user associated with the JWT token in the request.
    """

    def get(self, request):
        """Retrieve the current authenticated user's profile data.

        Args:
            request: HTTP request containing the authenticated user in
                request.user (injected by JWT authentication middleware).

        Returns:
            Response: HTTP 200 with the serialized user profile data
                including id, email, first_name, and last_name.
        """
        return Response(UserSerializer(request.user).data)
