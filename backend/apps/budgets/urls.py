from django.urls import path
from . import views

urlpatterns = [
    path('', views.BudgetListView.as_view(), name='budget-list'),
    path('create/', views.BudgetCreateView.as_view(), name='budget-create'),
    path('<int:pk>/update/', views.BudgetUpdateView.as_view(), name='budget-update'),
    path('<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='budget-delete'),
]
