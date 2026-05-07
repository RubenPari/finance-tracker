"""URL routing for the budgets application.

Defines the URL patterns that map to budget management API endpoints,
including list, create, update, and delete operations. All endpoints
require authentication and are scoped to the authenticated user.
"""

from django.urls import path
from . import views

urlpatterns = [
    # GET /api/budgets/ - List all budgets for the authenticated user
    path('', views.BudgetListView.as_view(), name='budget-list'),
    # POST /api/budgets/create/ - Create a new budget
    path('create/', views.BudgetCreateView.as_view(), name='budget-create'),
    # PUT/PATCH /api/budgets/<pk>/update/ - Update an existing budget
    path('<int:pk>/update/', views.BudgetUpdateView.as_view(), name='budget-update'),
    # DELETE /api/budgets/<pk>/delete/ - Delete an existing budget
    path('<int:pk>/delete/', views.BudgetDeleteView.as_view(), name='budget-delete'),
]
