from django.urls import path
from . import views

urlpatterns = [
    path('', views.CategoryListView.as_view(), name='category-list'),
    path('create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('ai-categorize/', views.AICategorizeView.as_view(), name='category-ai-categorize'),
    path('<int:pk>/update/', views.CategoryUpdateView.as_view(), name='category-update'),
    path('<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category-delete'),
    path('rules/', views.CategoryRuleListView.as_view(), name='rule-list'),
    path('rules/create/', views.CategoryRuleCreateView.as_view(), name='rule-create'),
    path('rules/<int:pk>/delete/', views.CategoryRuleDeleteView.as_view(), name='rule-delete'),
]
