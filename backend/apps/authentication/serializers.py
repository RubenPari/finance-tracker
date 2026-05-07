"""
Serializers for the authentication application.

Handles serialization and deserialization of user data for registration
and profile retrieval, including password validation and user creation logic.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration.

    Handles incoming registration data, validates password strength using
    Django's built-in validators, ensures password confirmation matches,
    and creates new user instances with email-based authentication.

    Attributes:
        password: Write-only field with Django password validation applied.
        password_confirm: Write-only field to verify password entry matches.
    """

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        # Include all registration fields; id is read-only output
        fields = ('id', 'email', 'password', 'password_confirm', 'first_name', 'last_name')

    def validate(self, data):
        """Cross-field validation to ensure passwords match.

        Compares the password and password_confirm fields to verify
        they are identical before proceeding with user creation.

        Args:
            data: Dictionary of validated form data containing at least
                'password' and 'password_confirm' keys.

        Returns:
            dict: The validated data if passwords match.

        Raises:
            serializers.ValidationError: If password and password_confirm
                do not match.
        """
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Le password non coincidono.'})
        return data

    def create(self, validated_data):
        """Create a new user instance with the validated data.

        Removes the password_confirm field (not needed on the User model),
        auto-generates a username from the email if not provided, and
        uses Django's create_user method which securely hashes the password.

        Args:
            validated_data: Dictionary of validated registration data
                including email, password, first_name, and last_name.

        Returns:
            User: The newly created user instance with hashed password.
        """
        # Remove confirmation field as it is not part of the User model
        validated_data.pop('password_confirm')
        # Auto-set username to match email for email-based authentication
        if 'username' not in validated_data:
            validated_data['username'] = validated_data['email']
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for serializing user profile data.

    Converts User model instances into JSON-serializable dictionaries
    for API responses, exposing only non-sensitive user information.
    Excludes password and other sensitive fields from output.
    """

    class Meta:
        model = User
        # Expose only safe profile fields, never password or internal data
        fields = ('id', 'email', 'first_name', 'last_name')
