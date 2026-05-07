"""
URL routing for the authentication application.

Defines the API endpoint routes for user authentication operations
including registration, login, token refresh, logout, and profile retrieval.
Uses Django REST Framework SimpleJWT views for token-based login/refresh.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    # POST: Register a new user account
    path('register/', views.RegisterView.as_view(), name='auth-register'),
    # POST: Obtain JWT access and refresh tokens with email/password
    path('login/', TokenObtainPairView.as_view(), name='auth-login'),
    # POST: Refresh an expired access token using a valid refresh token
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    # POST: Logout and invalidate the current refresh token
    path('logout/', views.LogoutView.as_view(), name='auth-logout'),
    # GET: Retrieve the authenticated user's profile information
    path('me/', views.MeView.as_view(), name='auth-me'),
]
