from rest_framework import generics, permissions, status # Ensure permissions is imported
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from django.utils import timezone
import datetime
from .models import (
    Profile,
    PersonalityQuestion,
    UserLocation,
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

class Connection(models.Model):
    """
    Represents a connection between two users that expires after one hour
    unless both users accept it.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'  # Initial state when created
        ACCEPTED = 'ACCEPTED', 'Accepted'  # User has accepted
        DECLINED = 'DECLINED', 'Declined'  # User has declined
        EXPIRED = 'EXPIRED', 'Expired'  # Connection has expired

    # The two users involved in the connection
    user1 = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='connections_as_user1'
    )
    user2 = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='connections_as_user2'
    )
    
    # Status fields for each user
    user1_status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    user2_status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # If connection is deleted or expired
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        # Ensure uniqueness between users (regardless of order)
        constraints = [
            models.UniqueConstraint(
                fields=['user1', 'user2'],
                name='unique_connection_users'
            ),
            models.CheckConstraint(
                check=~models.Q(user1=models.F('user2')),
                name='prevent_self_connection'
            )
        ]
        # Add indexes for performance
        indexes = [
            models.Index(fields=['user1', 'is_deleted', 'expires_at']),
            models.Index(fields=['user2', 'is_deleted', 'expires_at']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    # Custom managers
    class ConnectionManager(models.Manager):
        def get_queryset(self):
            # Filter out expired connections by default
            return super().get_queryset().filter(
                models.Q(expires_at__isnull=True) | 
                models.Q(expires_at__gt=timezone.now()),
                is_deleted=False
            )
        
        def with_expired(self):
            # Include expired connections when needed
            return super().get_queryset().filter(is_deleted=False)
        
        def expire_old_connections(self):
            """
            Mark connections that have passed their expiration time as expired
            This should be run via a scheduled task
            """
            now = timezone.now()
            expired = super().get_queryset().filter(
                expires_at__lt=now,
                is_deleted=False
            )
            count = expired.count()
            expired.update(is_deleted=True)
            return count
    
    # Set the managers
    objects = ConnectionManager()
    all_objects = models.Manager()  # Keep reference to standard manager
    
    def save(self, *args, **kwargs):
        # First time saving, set expiration one hour from now
        if not self.id and not self.expires_at:
            self.expires_at = timezone.now() + datetime.timedelta(hours=1)
        
        # Check if both users have accepted
        if self.user1_status == self.Status.ACCEPTED and self.user2_status == self.Status.ACCEPTED:
            self.expires_at = None  # Remove expiration if both accepted
        
        # If either has declined, mark as deleted
        if self.user1_status == self.Status.DECLINED or self.user2_status == self.Status.DECLINED:
            self.is_deleted = True
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if connection has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    @property
    def is_active(self):
        """Connection is active if it's not deleted and not expired"""
        return not self.is_deleted and not self.is_expired
    
    @property
    def is_mutual(self):
        """Check if connection is mutually accepted"""
        return (self.user1_status == self.Status.ACCEPTED and 
                self.user2_status == self.Status.ACCEPTED)
    
    def get_status_for_user(self, user):
        """Get connection status from perspective of given user"""
        if user.id == self.user1.id:
            return self.user1_status
        elif user.id == self.user2.id:
            return self.user2_status
        return None
    
    def set_status_for_user(self, user, status):
        """Set connection status for given user"""
        if user.id == self.user1.id:
            self.user1_status = status
        elif user.id == self.user2.id:
            self.user2_status = status
        else:
            raise ValueError("User is not part of this connection")
        self.save()
    
    def get_other_user(self, user):
        """Get the other user in the connection"""
        if user.id == self.user1.id:
            return self.user2
        elif user.id == self.user2.id:
            return self.user1
        return None
    
    @classmethod
    def get_active_connection(cls, user1, user2):
        """
        Get active connection between two users if it exists
        Returns None if no active connection
        """
        # Check both possible orders of users
        try:
            # Try user1, user2 order
            conn = cls.objects.filter(
                user1=user1, 
                user2=user2, 
                is_deleted=False
            ).exclude(
                expires_at__lt=timezone.now()
            ).first()
            
            if not conn:
                # Try user2, user1 order
                conn = cls.objects.filter(
                    user1=user2, 
                    user2=user1, 
                    is_deleted=False
                ).exclude(
                    expires_at__lt=timezone.now()
                ).first()
            
            return conn
        except cls.DoesNotExist:
            return None
    
    @classmethod
    def create_connection(cls, user1, user2):
        """
        Create a new connection between users if no active connection exists
        """
        # First check if active connection exists
        existing = cls.get_active_connection(user1, user2)
        if existing:
            return existing
        
        # Ensure consistent ordering of users (e.g., by user ID)
        # This helps with the uniqueness constraint
        if user1.id > user2.id:
            user1, user2 = user2, user1
            
        return cls.objects.create(user1=user1, user2=user2)
    
    @classmethod
    def get_pending_connections(cls, user):
        """Get all pending connections for a user"""
        now = timezone.now()
        return cls.objects.filter(
            models.Q(user1=user, user1_status=cls.Status.PENDING) |
            models.Q(user2=user, user2_status=cls.Status.PENDING),
            is_deleted=False
        ).exclude(
            expires_at__lt=now
        )
    
    @classmethod
    def get_mutual_connections(cls, user):
        """Get all mutual (accepted) connections for a user"""
        return cls.objects.filter(
            models.Q(
                user1=user, 
                user1_status=cls.Status.ACCEPTED,
                user2_status=cls.Status.ACCEPTED
            ) |
            models.Q(
                user2=user, 
                user1_status=cls.Status.ACCEPTED,
                user2_status=cls.Status.ACCEPTED
            ),
            is_deleted=False
        )
    
    def __str__(self):
        status = "Mutual" if self.is_mutual else "Pending"
        if self.is_deleted:
            status = "Deleted"
        elif self.is_expired:
            status = "Expired"
        return f"{status} connection between {self.user1} and {self.user2}"
        