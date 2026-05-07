"""
Django REST Framework serializers for the categories application.

Provides serialization for Category and CategoryRule models, including
read-only computed fields for related data display.
"""

from rest_framework import serializers
from .models import Category, CategoryRule


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for the Category model.

    Handles serialization and deserialization of category data for CRUD
    operations. The id, is_system, and user fields are read-only to
    prevent unauthorized modification of ownership or system flags.
    """

    class Meta:
        model = Category
        fields = ('id', 'name', 'color', 'icon', 'is_system', 'user')
        read_only_fields = ('id', 'is_system', 'user')


class CategoryRuleSerializer(serializers.ModelSerializer):
    """Serializer for the CategoryRule model.

    Includes denormalized category_name and category_color fields for
    frontend display without requiring additional API calls. These
    fields are read-only and sourced from the related Category model.
    """
    # Read-only fields sourced from the related Category for UI convenience
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)

    class Meta:
        model = CategoryRule
        fields = ('id', 'keyword', 'category', 'category_name', 'category_color', 'priority', 'created_at')
        read_only_fields = ('id', 'created_at')
