from rest_framework import generics, permissions, status # Ensure permissions is imported
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from django.utils import timezone
import datetime
from .models import (
    Profile,
    PersonalityQuestion,
    UserLocation,
    Connection,
)
from .serializers import (
    OnboardingSerializer,
    ProfileUpdateSerializer,
    PersonalityQuestionSerializer,
    UserLocationSerializer,
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

class UserLocationView(generics.GenericAPIView):
    """
    Endpoint for user location operations.
    GET: Retrieves the user's latest location
    POST: Creates a new location entry
    """
    serializer_class = UserLocationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests - return the user's latest location"""
        try:
            # Get the most recent location for this user
            location = UserLocation.objects.filter(
                user=self.request.user
            ).order_by('-last_updated').first()
            
            if location:
                serializer = self.get_serializer(location)
                return Response(serializer.data)
            else:
                # No location found
                return Response(
                    {"detail": "No location data found for this user."},
                    status=status.HTTP_404_NOT_FOUND
                )
        except Exception as e:
            return Response(
                {"detail": f"Error retrieving location: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests - create a new location entry and find nearby users"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        latitude = serializer.validated_data['latitude']
        longitude = serializer.validated_data['longitude']
        
        print(f"New location for {request.user} with lat {latitude} and long {longitude}")
        
        # Create a new location entry
        location = UserLocation.objects.create(
            user=request.user,
            latitude=latitude,
            longitude=longitude,
            is_active=serializer.validated_data.get('is_active', True)
        )

        # Create a new location entry
        location = UserLocation.objects.create(
            user=request.user,
            latitude=serializer.validated_data['latitude'],
            longitude=serializer.validated_data['longitude'],
            is_active=serializer.validated_data.get('is_active', True)
        )
    
        # Find nearby users
        nearby_users = UserLocation.find_nearby_users(
            user=request.user,
            latitude=latitude,
            longitude=longitude
        )

        # Create connections with nearby users
        new_connections = []
        for nearby_location in nearby_users:
            nearby_user = nearby_location.user

            # if XXXsomething_usersAreMatch(request.user, nearby_user) == False: continue

            # Check if there's an active connection already
            existing_connection = Connection.get_active_connection(request.user, nearby_user)
            if not existing_connection:
                # Create a new connection
                connection = Connection.create_connection(request.user, nearby_user)
                new_connections.append({
                    'user': nearby_user.username,
                    'distance': nearby_location.distance
                })
        
        
        result_serializer = self.get_serializer(location)
        response_data = result_serializer.data
        
        return Response(response_data, status=status.HTTP_201_CREATED)
