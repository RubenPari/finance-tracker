from django.urls import path
from . import views

urlpatterns = [
    path('summary/', views.SummaryView.as_view(), name='stats-summary'),
    path('by-category/', views.ByCategoryView.as_view(), name='stats-by-category'),
    path('monthly/', views.MonthlyTrendView.as_view(), name='stats-monthly'),
    path('top-merchants/', views.TopMerchantsView.as_view(), name='stats-top-merchants'),
    path('balance/', views.BalanceView.as_view(), name='stats-balance'),
    path('comparison/', views.ComparisonView.as_view(), name='stats-comparison'),
]
