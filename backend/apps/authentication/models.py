"""
User model definitions for the authentication application.

Defines a custom User model that extends Django's AbstractUser,
using email as the primary authentication identifier instead of username.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user model that uses email as the unique login identifier.

    Extends Django's AbstractUser to replace the default username-based
    authentication with email-based authentication. The email field is
    enforced as unique across all users.

    Attributes:
        email: Unique email address used for authentication.
        USERNAME_FIELD: Field name used as the unique identifier for login.
        REQUIRED_FIELDS: List of fields required when creating a superuser
            via createsuperuser command (empty since email is the sole identifier).
    """

    email = models.EmailField(unique=True)

    # Configure email as the primary authentication field instead of username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'

    def __str__(self):
        """Return the string representation of the user.

        Returns:
            str: The user's email address.
        """
        return self.email
