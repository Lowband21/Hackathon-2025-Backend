# backend/api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import (
    Profile,
    Interest,
    Course,
    Club,
    Major,
    Minor, # Added Major, Minor
    PersonalityQuestion,
    PersonalityAnswer,
    UserLocation
)

User = get_user_model()

# --- Serializer for Personality Questions (Read Only) ---
class PersonalityQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalityQuestion
        fields = ['id', 'text', 'order']

# --- Serializers for Onboarding (Complex Nested Write) ---
class OnboardingPersonalityAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer_score = serializers.IntegerField(min_value=1, max_value=5)

# Custom RelatedField for simple name-based creation/lookup
class NameRelatedField(serializers.RelatedField):
    """
    A custom field to use for representing the target of the relationship
    by a unique 'name' attribute. Handles get_or_create.
    """
    def __init__(self, related_model, **kwargs):
        self.related_model = related_model
        # Ensure queryset is provided for RelatedField initialization
        super().__init__(queryset=related_model.objects.all(), **kwargs)

    def to_internal_value(self, data):
        # Assumes data is the 'name' of the related object
        # Handles get_or_create based on the 'name' field.
        try:
            instance, created = self.related_model.objects.get_or_create(name=data)
            return instance
        except (TypeError, ValueError):
            self.fail('invalid')
        except self.related_model.MultipleObjectsReturned:
             # Handle cases where name is not unique if necessary, though models define it as unique
             # For Course, this might need adjustment if name alone isn't the intended lookup key
             self.fail('multiple_matches', input=data)


    def to_representation(self, value):
        # Represents the object by its name attribute
        return getattr(value, 'name', None)

# Specific field for Courses, using NameRelatedField for now
# Future enhancement: Accept dict {'name': 'X', 'department': 'Y', 'course_number': 'Z'}
class CourseRelatedField(NameRelatedField):
     pass


class OnboardingSerializer(serializers.ModelSerializer):
    # User fields
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    email = serializers.EmailField(required=True) # Assuming email is used for login/uniqueness
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    preferred_name = serializers.CharField(required=False, allow_blank=True) # Already on CustomUser

    # Profile fields (source removed, handled in create)
    image = serializers.ImageField(required=False, source='profile.image')
    year_in_school = serializers.ChoiceField(choices=Profile.AcademicYear.choices, required=False, allow_null=True)
    department = serializers.CharField(required=False, allow_blank=True)
    socials = serializers.JSONField(required=False, allow_null=True)

    # ManyToMany fields for Profile (source removed, handled in create)
    majors = NameRelatedField(related_model=Major, many=True, required=False)
    minors = NameRelatedField(related_model=Minor, many=True, required=False)
    interests = NameRelatedField(related_model=Interest, many=True, required=False)
    courses_taking = CourseRelatedField(related_model=Course, many=True, required=False)
    favorite_courses = CourseRelatedField(related_model=Course, many=True, required=False)
    clubs = NameRelatedField(related_model=Club, many=True, required=False)

    # Nested write for personality answers
    personality_answers = OnboardingPersonalityAnswerSerializer(many=True, write_only=True, required=True)

    class Meta:
        model = User
        # Updated fields list
        fields = [
            'email', 'password', 'first_name', 'last_name', 'preferred_name',
            'image', 'year_in_school', 'department', 'socials', # Profile fields sourced
            'majors', 'minors', 'interests', 'courses_taking', 'favorite_courses', 'clubs', # M2M fields sourced
            'personality_answers' # Nested write field
        ]
        # Note: 'profile.' sourced fields are handled by the serializer logic

    def create(self, validated_data):
        # Extract profile-related data before User creation
        profile_related_data = {
            'image': validated_data.pop('image', None) if 'image' in validated_data else None,
            'year_in_school': validated_data.pop('year_in_school', None),
            'department': validated_data.pop('department', ''),
            'socials': validated_data.pop('socials', {}),
            'majors_data': validated_data.pop('majors', []),
            'minors_data': validated_data.pop('minors', []),
            'interests_data': validated_data.pop('interests', []),
            'courses_taking_data': validated_data.pop('courses_taking', []),
            'favorite_courses_data': validated_data.pop('favorite_courses', []),
            'clubs_data': validated_data.pop('clubs', []),
        }
        personality_answers_data = validated_data.pop('personality_answers')

        # Explicitly define User fields based on serializer definition
        user_field_names = ['email', 'password', 'first_name', 'last_name', 'preferred_name']
        user_data = {k: v for k, v in validated_data.items() if k in user_field_names}

        with transaction.atomic():
            # Create User instance using only user-specific data
            user = User.objects.create_user(**user_data)

            # Create Profile instance, linking to the user
            profile_direct_fields = {
                k: v for k, v in profile_related_data.items()
                if not k.endswith('_data')
            }
            profile = Profile.objects.create(user=user, **profile_direct_fields)

            # Set ManyToMany relationships for the profile
            profile.majors.set(profile_related_data['majors_data'])
            profile.minors.set(profile_related_data['minors_data'])
            profile.interests.set(profile_related_data['interests_data'])
            profile.courses_taking.set(profile_related_data['courses_taking_data'])
            profile.favorite_courses.set(profile_related_data['favorite_courses_data'])
            profile.clubs.set(profile_related_data['clubs_data'])

            # Create PersonalityAnswer instances
            answers_to_create = []
            for answer_data in personality_answers_data:
                try:
                    question = PersonalityQuestion.objects.get(pk=answer_data['question_id'])
                    answers_to_create.append(
                        PersonalityAnswer(
                            profile=profile,
                            question=question,
                            answer_score=answer_data['answer_score']
                        )
                    )
                except PersonalityQuestion.DoesNotExist:
                    raise serializers.ValidationError(
                        f"PersonalityQuestion with id {answer_data['question_id']} does not exist."
                    )
            PersonalityAnswer.objects.bulk_create(answers_to_create)

        return user # Return the created user instance

# --- Serializer for Profile Update (PATCH) ---
class ProfileUpdateSerializer(serializers.ModelSerializer):
    # Use the same related fields as in OnboardingSerializer for consistency
    image = serializers.ImageField(required=False)
    majors = NameRelatedField(related_model=Major, many=True, required=False)
    minors = NameRelatedField(related_model=Minor, many=True, required=False)
    interests = NameRelatedField(related_model=Interest, many=True, required=False)
    courses_taking = CourseRelatedField(related_model=Course, many=True, required=False)
    favorite_courses = CourseRelatedField(related_model=Course, many=True, required=False)
    clubs = NameRelatedField(related_model=Club, many=True, required=False)
    year_in_school = serializers.ChoiceField(choices=Profile.AcademicYear.choices, required=False, allow_null=True)

    class Meta:
        model = Profile
        # Updated fields list for PATCHable profile attributes
        fields = [
            'image', 'year_in_school', 'department', 'socials',
            'majors', 'minors', 'interests', 'courses_taking', 'favorite_courses', 'clubs'
        ]
        read_only_fields = ['user'] # User should not be changed via this serializer

    # Default update handles partial updates (PATCH) correctly for direct fields.
    # For M2M fields, DRF's default update replaces the entire set.

# Serlializer for the user location ping 
class UserLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLocation
        fields = ['latitude', 'longitude', 'last_updated', 'is_active']
        read_only_fields = ['last_updated']
