from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings # To link to the user model cleanly
from django.core.validators import MinValueValidator, MaxValueValidator # Import validators

# 1. Custom User (Extending Django's default)
class CustomUser(AbstractUser):
    preferred_name = models.CharField(max_length=150, blank=True, verbose_name="Preferred Name")
    # Add related_name to resolve clashes with default User model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="customuser_set", # Unique related_name
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set", # Unique related_name
        related_query_name="customuser",
    )
    # Ensure email is unique if using it for login instead of username
    # email = models.EmailField(unique=True)
    def __str__(self): return self.username

# 2. Supporting Models for Profile (Many-to-Many or Lookups)
class Interest(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

# New Major Model
class Major(models.Model):
    name = models.CharField(max_length=150, unique=True)
    def __str__(self): return self.name

# New Minor Model
class Minor(models.Model):
    name = models.CharField(max_length=150, unique=True)
    def __str__(self): return self.name

class Course(models.Model):
    name = models.CharField(max_length=150) # Name might not be unique when considering course number
    department = models.CharField(max_length=100, blank=True)
    course_number = models.CharField(max_length=20, blank=True) # Added course number
    class Meta:
        unique_together = ('department', 'course_number', 'name') # Ensure combination is unique
        ordering = ['department', 'course_number']
    def __str__(self):
        return f"{self.department} {self.course_number}: {self.name}" if self.department and self.course_number else self.name

class Club(models.Model):
    name = models.CharField(max_length=150, unique=True)
    def __str__(self): return self.name

# 3. Personality Quiz Models
class PersonalityQuestion(models.Model):
    text = models.TextField(unique=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    class Meta: ordering = ['order']
    def __str__(self): return self.text[:50] + "..."

# 4. User Profile (Central Hub for User Data)
class Profile(models.Model):
    class AcademicYear(models.TextChoices):
        FRESHMAN = 'FR', 'Freshman'
        SOPHOMORE = 'SO', 'Sophomore'
        JUNIOR = 'JR', 'Junior'
        SENIOR = 'SR', 'Senior'
        GRADUATE = 'GR', 'Graduate'
        OTHER = 'OT', 'Other'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    # Removed major CharField, replaced with ManyToManyField below
    year_in_school = models.CharField(
        max_length=2,
        choices=AcademicYear.choices,
        blank=True,
        null=True, # Allow blank/null if user doesn't specify
    )
    department = models.CharField(max_length=100, blank=True) # Keep department if relevant outside major/minor context
    majors = models.ManyToManyField(Major, blank=True) # Replaced single major
    minors = models.ManyToManyField(Minor, blank=True) # Added minors
    interests = models.ManyToManyField(Interest, blank=True)
    courses_taking = models.ManyToManyField(Course, blank=True, related_name='students_taking')
    favorite_courses = models.ManyToManyField(Course, blank=True, related_name='favorited_by')
    clubs = models.ManyToManyField(Club, blank=True)
    socials = models.JSONField(blank=True, null=True, default=dict, help_text='e.g., {"instagram": "username", "snapchat": "username", "x": "handle"}') # Updated help text
    def __str__(self): return f"Profile for {self.user.username}"

# 5. Personality Answers (Linking User, Question, and their Answer)
class PersonalityAnswer(models.Model):
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='personality_answers')
    question = models.ForeignKey(PersonalityQuestion, on_delete=models.CASCADE)
    answer_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], # Example: 1-5 scale
        help_text="User's answer score (e.g., 1-5)"
    )
    class Meta: unique_together = ('profile', 'question')
    def __str__(self): return f"Answer by {self.profile.user.username} to Q{self.question.id}"
