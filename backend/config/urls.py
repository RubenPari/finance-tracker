"""Root URL configuration for the Finance Tracker API.

Routes all API endpoints under the `/api/` prefix to their
respective app-level URL configurations. The Django admin
interface is available at `/admin/`.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.authentication.urls')),
    path('api/transactions/', include('apps.transactions.urls')),
    path('api/categories/', include('apps.categories.urls')),
    path('api/budgets/', include('apps.budgets.urls')),
    path('api/stats/', include('apps.stats.urls')),
    path('api/suggestions/', include('apps.suggestions.urls')),
]
