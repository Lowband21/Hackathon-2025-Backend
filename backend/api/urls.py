# backend/api/urls.py
from django.urls import path
from .views import (
    OnboardingView,
    UserProfileView,
    PersonalityQuestionListView,
)

app_name = 'api' # Namespace for the API urls

urlpatterns = [
    # POST /api/onboarding/ -> Creates a new user and profile
    path('onboarding/', OnboardingView.as_view(), name='onboarding'),

    # GET, PATCH /api/profile/me/ -> Retrieves or updates the authenticated user's profile
    path('profile/me/', UserProfileView.as_view(), name='profile-me'),

    # GET /api/personality-questions/ -> Lists available personality questions
    path('personality-questions/', PersonalityQuestionListView.as_view(), name='personality-questions'),
]