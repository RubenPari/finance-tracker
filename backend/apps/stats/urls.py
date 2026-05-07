"""URL routing for the stats application.

Defines the URL patterns that map to the statistics and analytics API views.
All routes are prefixed with the stats app namespace in the root URL configuration.

URL Patterns:
    summary/      - Overall financial summary (income, expenses, net).
    by-category/  - Expense breakdown by category.
    monthly/      - Monthly income and expense trends.
    top-merchants/ - Highest-spending merchants/descriptions.
    balance/      - Historical balance over time.
    comparison/   - Category spending comparison between periods.
    subscriptions/ - Detected recurring subscriptions with analytics.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('summary/', views.SummaryView.as_view(), name='stats-summary'),
    path('by-category/', views.ByCategoryView.as_view(), name='stats-by-category'),
    path('monthly/', views.MonthlyTrendView.as_view(), name='stats-monthly'),
    path('top-merchants/', views.TopMerchantsView.as_view(), name='stats-top-merchants'),
    path('balance/', views.BalanceView.as_view(), name='stats-balance'),
    path('comparison/', views.ComparisonView.as_view(), name='stats-comparison'),
    path('subscriptions/', views.SubscriptionsView.as_view(), name='stats-subscriptions'),
]
