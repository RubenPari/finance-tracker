from django.urls import path
from . import views

urlpatterns = [
    path('', views.SuggestionsView.as_view(), name='suggestions'),
]
