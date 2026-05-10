from decimal import Decimal
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from apps.categories.models import Category
from apps.transactions.models import Transaction


User = get_user_model()


class StatsViewsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='stats-user',
            email='stats@example.com',
            password='test-password-123',
        )
        self.client.force_authenticate(user=self.user)

        self.food = Category.objects.create(
            user=self.user,
            name='Food',
            color='#10B981',
            icon='shopping-cart',
            is_system=False,
        )

    def _create_expense(self, when: datetime, description: str, amount: str, category: Category | None = None):
        aware_when = timezone.make_aware(when) if timezone.is_naive(when) else when
        return Transaction.objects.create(
            user=self.user,
            started_at=aware_when,
            completed_at=aware_when,
            description=description,
            amount=Decimal(amount),
            fee=Decimal('0'),
            currency='EUR',
            transaction_type='Pagamento',
            state='COMPLETATO',
            category=category,
        )

    def test_top_merchants_orders_by_highest_spending_first(self):
        now = timezone.now()
        current_month = now.replace(day=10, hour=10, minute=0, second=0, microsecond=0)

        self._create_expense(current_month, 'Amazon', '-10.00')
        self._create_expense(current_month, 'Starbucks', '-40.00')
        self._create_expense(current_month, 'Ikea', '-20.00')

        response = self.client.get('/api/stats/top-merchants/?period=month&limit=2')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['merchant'], 'Starbucks')
        self.assertEqual(response.data[0]['total'], 40.0)
        self.assertEqual(response.data[1]['merchant'], 'Ikea')
        self.assertEqual(response.data[1]['total'], 20.0)

    def test_comparison_uses_calendar_aware_previous_month_window(self):
        now = timezone.now()
        this_month = now.replace(day=12, hour=9, minute=0, second=0, microsecond=0)
        prev_month = this_month - timedelta(days=31)

        self._create_expense(this_month, 'Spesa attuale', '-100.00', category=self.food)
        self._create_expense(prev_month, 'Spesa precedente', '-50.00', category=self.food)

        response = self.client.get('/api/stats/comparison/?period=month')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 1)

        food_row = next(item for item in response.data if item['category'] == 'Food')
        self.assertEqual(food_row['current'], 100.0)
        self.assertEqual(food_row['previous'], 50.0)
        self.assertEqual(food_row['change_pct'], 100.0)

    def test_comparison_custom_range_uses_same_length_previous_window(self):
        self._create_expense(datetime(2026, 4, 15, 12, 0), 'Current Window', '-120.00', category=self.food)
        self._create_expense(datetime(2026, 4, 5, 12, 0), 'Previous Window', '-60.00', category=self.food)
        # Outside previous mirrored window: should not be counted
        self._create_expense(datetime(2026, 3, 20, 12, 0), 'Outside Previous', '-999.00', category=self.food)

        response = self.client.get('/api/stats/comparison/?date_from=2026-04-10&date_to=2026-04-20')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        food_row = next(item for item in response.data if item['category'] == 'Food')
        self.assertEqual(food_row['current'], 120.0)
        self.assertEqual(food_row['previous'], 60.0)
        self.assertEqual(food_row['change_pct'], 100.0)

    def test_invalid_period_returns_400(self):
        response = self.client.get('/api/stats/summary/?period=weekly')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('period', response.data)

    def test_invalid_months_returns_400(self):
        response = self.client.get('/api/stats/monthly/?months=abc')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('months', response.data)
