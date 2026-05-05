from rest_framework import serializers
from .models import Category, CategoryRule


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'color', 'icon', 'is_system', 'user')
        read_only_fields = ('id', 'is_system', 'user')


class CategoryRuleSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_color = serializers.CharField(source='category.color', read_only=True)

    class Meta:
        model = CategoryRule
        fields = ('id', 'keyword', 'category', 'category_name', 'category_color', 'priority', 'created_at')
        read_only_fields = ('id', 'created_at')
