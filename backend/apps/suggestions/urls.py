"""URL routing configuration for the suggestions application.

Maps the root URL of this app to the SuggestionsView class-based view,
which handles GET requests to return personalized finance suggestions.
"""

from django.urls import path
from . import views

# URL pattern list for the suggestions app.
# The empty string '' means this view is served at the app's base path.
urlpatterns = [
    path('', views.SuggestionsView.as_view(), name='suggestions'),
]
