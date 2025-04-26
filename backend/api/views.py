from rest_framework import generics, permissions # Ensure permissions is imported
from django.contrib.auth import get_user_model
from .models import Profile, PersonalityQuestion
from .serializers import (
    OnboardingSerializer,
    ProfileUpdateSerializer,
    PersonalityQuestionSerializer,
)

User = get_user_model()

# --- View for Onboarding (POST) ---
class OnboardingView(generics.CreateAPIView):
    """
    Handles new user registration and initial profile setup, including personality answers.
    Accessible by anyone.
    """
    queryset = User.objects.all()
    serializer_class = OnboardingSerializer
    permission_classes = [permissions.AllowAny] # Anyone can create a new user account

# --- View for Personality Questions (GET) ---
class PersonalityQuestionListView(generics.ListAPIView):
    """
    Provides a list of all available personality questions, ordered by 'order'.
    Accessible by anyone.
    """
    queryset = PersonalityQuestion.objects.all().order_by('order')
    serializer_class = PersonalityQuestionSerializer
    permission_classes = [permissions.AllowAny] # Anyone can view the questions

# --- View for User Profile (GET, PATCH) ---
class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Allows authenticated users to retrieve (GET) and update (PATCH) their own profile.
    """
    queryset = Profile.objects.all() # Base queryset
    serializer_class = ProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated] # Only logged-in users can access

    def get_object(self):
        """
        Overrides the default get_object to return the profile associated with the
        currently authenticated user (request.user). Creates a profile if one
        doesn't exist yet for the user.
        """
        # Use get_or_create to handle cases where a user might exist but not have a profile yet
        # (e.g., created via createsuperuser or if onboarding failed mid-way)
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
