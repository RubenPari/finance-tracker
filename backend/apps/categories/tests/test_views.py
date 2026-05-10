from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase


User = get_user_model()


class CategoriesViewsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='categories-user',
            email='categories@example.com',
            password='test-password-123',
        )
        self.client.force_authenticate(user=self.user)

    def test_ai_categorize_invalid_limit_returns_400(self):
        response = self.client.post('/api/categories/ai-categorize/?limit=abc')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('limit', response.data)

    def test_ai_categorize_out_of_range_limit_returns_400(self):
        response = self.client.post('/api/categories/ai-categorize/?limit=0')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('limit', response.data)
