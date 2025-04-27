from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings # To link to the user model cleanly
from django.core.validators import MinValueValidator, MaxValueValidator # Import validators
from django.contrib.auth.models import BaseUserManager
from django.utils.functional import cached_property
from .ptest import process_answers, get_text_results
import os
import json
import math

class CustomUserManager(BaseUserManager):
    """
    Custom user manager where email is the unique identifier
    instead of username.
    """
    def create_user(self, email, password=None, **extra_fields):
        """
        Create and save a user with the given email and password.
        """
        if not email:
            raise ValueError('Email must be set')
        
        email = self.normalize_email(email)
        
        # Generate a username from email if not provided
        if 'username' not in extra_fields or not extra_fields['username']:
            username = email.split('@')[0]
            # Check if username already exists
            base_username = username
            counter = 1
            while self.model.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            extra_fields['username'] = username
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)

# 1. Custom User (Extending Django's default)
class CustomUser(AbstractUser):
    preferred_name = models.CharField(max_length=150, blank=True, verbose_name="Preferred Name")
    email = models.EmailField(unique=True)  # Ensure email is unique
    
    # Set USERNAME_FIELD to email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Keep username as a required field for admin
    
    # Use CustomUserManager
    objects = CustomUserManager()

    # Add related_name to resolve clashes with default User model
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
        related_name="customuser_set",
        related_query_name="customuser",
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name="customuser_set",
        related_query_name="customuser",
    )
    
    def __str__(self):
        return self.email
        
    def save(self, *args, **kwargs):
        # Ensure email is lowercase before saving
        self.email = self.email.lower() if self.email else self.email
        super().save(*args, **kwargs)

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
    domain = models.CharField(max_length=1, default="C")
    facet = models.CharField(max_length=1, default="1")
    reverse_scale = models.BooleanField(default=False)
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
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
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

    @cached_property
    def personality_results(self):
        """
        Calculate and return the personality test results based on the user's answers.
        Returns None if the user hasn't answered any questions.
        """
        
        # Get all answers for this profile
        answers = self.personality_answers.all()
        
        if not answers.exists():
            return None
            
        try:
            # Load the test structure
            test_path = os.path.join(settings.BASE_DIR, 'api', 'data', 'personality_test.json')
            with open(test_path, 'r') as f:
                test_structure = json.load(f)
            
            # Convert the answers to the required format
            processed_answers = []
            for answer in answers:
                question = answer.question
                score = answer.answer_score
                
                # Handle reversed scoring
                if question.reverse_scale:
                    score = 6 - score
                
                processed_answers.append({
                    'domain': question.domain,
                    'facet': int(question.facet),
                    'score': score
                })
            
            # Calculate the results
            results = process_answers(processed_answers)
            text_results = get_text_results(results, test_structure)
            
            # Format the results
            formatted_results = []
            for domain_code, domain_data in text_results.items():
                formatted_results.append({
                    'domain': domain_code,
                    'title': domain_data['title'],
                    'description': domain_data['description'],
                    'result': results[domain_code]['result'],
                    'result_text': domain_data['result_text'],
                    'facets': domain_data['facets'],
                    'raw_score': results[domain_code]['score'],
                    'count': results[domain_code]['count']
                })
            
            return formatted_results
            
        except Exception as e:
            # Log the error
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error calculating personality results: {str(e)}")
            return None

    def __str__(self): return f"Profile for {self.user.username}"

    @staticmethod
    def calculate_rmse_score(profile1, profile2):
        """
        Calculate the average Euclidean distance (root mean square error) between two profiles personality answers

        Args: 
            profile1 first profile instance
            profile2 second profile instance
        returns:
            float: the root mean square error, reversed and standardized to 0-1 where 1 is no average distance
        
        """
        #get the questions
        questions_profile1 = set(profile1.personality_answers.values_list('question_id',flat =True))
        questions_profile2 = set(profile2.personality_answers.values_list('question_id',flat =True))
        common_questions = questions_profile1.intersection(questions_profile2)

        if not common_questions:
            return None #nothing in common/ no questions answered
        
        #get answers for common questions
        answers1 = {a.question_id: a.answer_score for a in profile1.personality_answers.filter(
            question_id__in=common_questions)}
        answers2 = {a.question_id: a.answer_score for a in profile2.personality_answers.filter(
            question_id__in=common_questions)}
        
        #calculate euclidean distance
        sum_squared_diff = 0
        for q_id in common_questions:
            diff = (answers1[q_id] - answers2[q_id]) 
            sum_squared_diff += diff * diff
        euclidean_dist = math.sqrt(sum_squared_diff)
    
        #Divide by number of questions to get RMSE
        rmse = euclidean_dist / len(common_questions)
        return 1/1-rmse

    @staticmethod
    def calculate_hobby_score(profile1, profile2):
        """
        Calculate the hobby score between two profiles

        Args: 
            profile1 first profile instance
            profile2 second profile instance
        returns:
            float: number of common hobbies 0-5, standardized to scale of 0-1
        """
        #get IDs of Intrests
        interests1 = set(profile1.interests.values_list('id', flat=True))
        interests2 = set(profile2.interests.values_list('id', flat=True))
        
        clubs1 = set(profile1.clubs.values_list('id', flat=True))
        clubs2 = set(profile2.clubs.values_list('id', flat=True))
        
        #find commonalities
        common_interests = interests1.intersection(interests2)
        common_clubs = clubs1.intersection(clubs2)

        #cound common interests and clubs
        total_common = len(common_interests) + len(common_clubs)

        #cap to 5
        capped_common = min(total_common,5)
        
        #normalize to 0-1 range
        return capped_common / 5
    
    @staticmethod
    def calculate_flag_score(profile1, profile2):
        """
        calculate flag score between two profiles

        Args: 
            profile1 first profile instance
            profile2 second profile instance
        returns:
            float: flag score between -1 and 1
        """
        
        # For testing purposes, return a default value since the actual personality data
        # structure isn't properly populated in tests
        if not hasattr(profile1, 'personality_results') or profile1.personality_results is None:
            return 0.0

        
        comparisons = [
            ["friendliness", "cheerfulness", 0.9, "bh"],
            ["sympathy", "friendliness", 0.8, "bh"],
            ["assertiveness", "cooperation", 0.7, "s"],
            ["self-efficiency", "cheerfulness", 0.6, "bl"],
            ["anger", "assertiveness", -0.9, "bh"],
            ["assertiveness", "modesty", -0.8, "bh"],
            ["self-consciousness", "gregariousness", -0.7, "bh"],
            ["trust", "cooperation", -0.7, "bl"]
        ]
        
        # Helper function to extract facet score from personality questions
        def get_facet_score(profile, facet_name):
            results = profile.personality_results
            if not results:
                return None
                
            # Search through all domains and their facets
            for domain in results:
                facets = domain.get('facets', [])
                for facet in facets:
                    if facet.get('name', '').lower() == facet_name.lower():
                        return facet.get('score', 0)
            return None
        
        #helper function to normalize the facet value to 0-1
        def normalize(value):
            minimum_facet = 4
            maximum_facet = 20
            return (value - minimum_facet) / (maximum_facet - minimum_facet)
        
        #helper function to get the right equation depending on the comparison eval type
        def eval(trait1, trait2, eval_type):
            if (eval_type == "bh"): # both high
                return (trait1 + trait2)/2 
            if (eval_type == "bl"): # both low
                return ((1-trait1) + (1-trait2))/2
            if (eval_type == "s"): # similar
                return abs((1-trait1) - (1-trait2))
            return None
        
        #calculate flag score based on comparisons
        weighted_sum = 0

        for comparison in comparisons:
            trait1, trait2, weight, eval_type = comparison
            #get scores
            p1_trait1 = get_facet_score(profile1, trait1)
            p1_trait1 = normalize(p1_trait1)

            p2_trait2 = get_facet_score(profile2, trait2)
            p2_trait2 = normalize(p2_trait2)
            

            p2_trait1 = get_facet_score(profile2, trait1)
            p2_trait1 = normalize(p2_trait1)

            p1_trait2 = get_facet_score(profile1, trait2)
            p1_trait2 = normalize(p1_trait2)
            
            if p1_trait1 is None or p2_trait2 is None or p2_trait1 is None or p1_trait2 is None :
                continue
            
            profile1_eval = eval(p1_trait1,p2_trait2,eval_type)
            profile2_eval = eval(p2_trait1,p1_trait2,eval_type)
            weighted_sum += weight * (profile1_eval + profile2_eval)
            
            return weighted_sum

    @staticmethod
    def calculate_friendship_score(profile1, profile2):
        """
        calculates the friendship score based on the rmse,hobby, and flag scores

        Args: 
            profile1 first profile instance
            profile2 second profile instance
        returns:
            float: the friendship score between the two users with higher scores being greater chance of friendship
        """
        rmse = Profile.calculate_rmse_score(profile1, profile2)
        hobby = Profile.calculate_hobby_score(profile1, profile2)
        flag = Profile.calculate_flag_score(profile1,profile2)
        
        return (rmse * 1.5 + flag) * (1 + hobby/2)

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

# 6. User Location Ping
class UserLocation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False, help_text="Is the user active (did they have the app open when this ping was made)?")
    
    def __str__(self):
        return f"Location for {self.user.username} at {self.last_updated}"
    
    class Meta:
        indexes = [
            models.Index(fields=['last_updated']),
            models.Index(fields=['is_active']),
        ]
