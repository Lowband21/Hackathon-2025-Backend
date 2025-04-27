from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import PersonalityQuestion, Profile, PersonalityAnswer

class PersonalityQuestionTests(APITestCase):
    """
    Tests for the Personality Questions endpoint.
    """
    @classmethod
    def setUpTestData(cls):
        """Set up non-modified objects used by all test methods."""
        PersonalityQuestion.objects.create(text="What is your favorite color?")
        PersonalityQuestion.objects.create(text="Are you a morning person or a night owl?")

    def test_get_personality_questions_list(self):
        """
        Ensure we can retrieve the list of personality questions.
        """
        url = reverse('api:personality-questions') # Use the namespaced URL name
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['text'], "What is your favorite color?")
        self.assertEqual(response.data[1]['text'], "Are you a morning person or a night owl?")

# Add more test classes below for other endpoints (Onboarding, Auth, Profile)

class OnboardingTests(APITestCase):
    """
    Tests for the User Onboarding endpoint.
    """
    @classmethod
    def setUpTestData(cls):
        """Set up non-modified objects used by all test methods."""
        cls.q1 = PersonalityQuestion.objects.create(text="Introvert or Extrovert?", order=1)
        cls.q2 = PersonalityQuestion.objects.create(text="Planner or Spontaneous?", order=2)
        # We don't strictly need to pre-create Interests, Courses, etc.
        # because the NameRelatedField handles get_or_create.

    def test_successful_onboarding(self):
        """
        Ensure a user can be successfully onboarded with valid data.
        """
        url = reverse('api:onboarding')
        payload = {
            "email": "test@example.com",  # This is required
            "password": "strongpassword123",
            "first_name": "Test",
            "last_name": "User",
            "preferred_name": "Tester",
            "year_in_school": Profile.AcademicYear.SOPHOMORE,
            "department": "Computer Science",
            "socials": {"linkedin": "testuser"},
            "majors": ["Computer Science", "Mathematics"],
            "minors": ["Physics"],
            "interests": ["Board Games", "Hiking", "Programming"],
            "courses_taking": ["COMP 2800", "MATH 3100"],
            "favorite_courses": ["COMP 1800"],
            "clubs": ["Coding Club", "Board Game Club"],
            "personality_answers": [
                {"question_id": self.q1.id, "answer_score": 2},
                {"question_id": self.q2.id, "answer_score": 4}
            ]
        }

        response = self.client.post(url, payload, format='json')
        
        # For debugging
        if response.status_code != status.HTTP_201_CREATED:
            print(f"Onboarding error: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        
        # Check if user was created by email instead of username
        User = get_user_model()
        self.assertTrue(User.objects.filter(email="test@example.com").exists())
        user = User.objects.get(email="test@example.com")
        self.assertTrue(hasattr(user, 'profile'))
        profile = user.profile

        # 3. Check basic profile fields
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertEqual(user.preferred_name, "Tester")
        self.assertEqual(profile.year_in_school, Profile.AcademicYear.SOPHOMORE)
        self.assertEqual(profile.department, "Computer Science")
        self.assertEqual(profile.socials, {"linkedin": "testuser"})

        # 4. Check M2M fields (using count and checking one value for brevity)
        self.assertEqual(profile.majors.count(), 2)
        self.assertTrue(profile.majors.filter(name="Computer Science").exists())
        self.assertEqual(profile.minors.count(), 1)
        self.assertTrue(profile.minors.filter(name="Physics").exists())
        self.assertEqual(profile.interests.count(), 3)
        self.assertTrue(profile.interests.filter(name="Hiking").exists())
        self.assertEqual(profile.courses_taking.count(), 2)
        self.assertTrue(profile.courses_taking.filter(name="COMP 2800").exists())
        self.assertEqual(profile.favorite_courses.count(), 1)
        self.assertTrue(profile.favorite_courses.filter(name="COMP 1800").exists())
        self.assertEqual(profile.clubs.count(), 2)
        self.assertTrue(profile.clubs.filter(name="Coding Club").exists())

        # 5. Check personality answers
        self.assertEqual(profile.personality_answers.count(), 2)
        self.assertTrue(profile.personality_answers.filter(question=self.q1, answer_score=2).exists())
        self.assertTrue(profile.personality_answers.filter(question=self.q2, answer_score=4).exists())

    # Add tests for invalid onboarding data (missing fields, bad email, etc.) later

from django.contrib.auth import get_user_model # Add this import if not already present

class AuthTests(APITestCase):
    """
    Tests for the JWT Authentication endpoints.
    """
    @classmethod
    def setUpTestData(cls):
        """Set up a test user."""
        cls.User = get_user_model()
        cls.test_username = 'authuser'
        cls.test_password = 'authpassword123'
        cls.test_user = cls.User.objects.create_user(
            username=cls.test_username,
            password=cls.test_password,
            email='auth@example.com'
        )
        # Create a profile for the user, as some views might implicitly expect it
        Profile.objects.create(user=cls.test_user)


    def test_obtain_token_pair_success(self):
        """
        Ensure valid credentials return an access and refresh token.
        """
        url = reverse('token_obtain_pair')  # This looks for the URL name, which is correct
        payload = {
            'email': 'auth@example.com',  # Changed from username to email
            'password': self.test_password,
        }
        response = self.client.post(url, payload, format='json')
        
        # For debugging
        if response.status_code != status.HTTP_200_OK:
            print(f"Token error response: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_obtain_token_pair_invalid_credentials(self):
        """
        Ensure invalid credentials return a 401 Unauthorized error.
        """
        url = reverse('token_obtain_pair')
        payload = {
            'email': 'auth@example.com',  # Changed from username to email
            'password': 'wrongpassword',
        }
        response = self.client.post(url, payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token_success(self):
        """
        Ensure a valid refresh token returns a new access token.
        """
        # First, obtain an initial token pair to get a refresh token
        obtain_url = reverse('token_obtain_pair')
        # Change this line to use email instead of username
        obtain_payload = {'email': 'auth@example.com', 'password': self.test_password}
        obtain_response = self.client.post(obtain_url, obtain_payload, format='json')
        
        # For debugging
        if obtain_response.status_code != status.HTTP_200_OK:
            print(f"Refresh token obtain error: {obtain_response.data}")
            
        self.assertEqual(obtain_response.status_code, status.HTTP_200_OK)
        refresh_token = obtain_response.data.get('refresh')
        self.assertIsNotNone(refresh_token, "Failed to get refresh token in setup for refresh test")

        # Now, use the refresh token
        refresh_url = reverse('token_refresh')
        refresh_payload = {
            'refresh': refresh_token
        }
        response = self.client.post(refresh_url, refresh_payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertNotIn('refresh', response.data) # Refresh endpoint only returns access token

    def test_refresh_token_invalid_token(self):
        """
        Ensure an invalid or expired refresh token returns a 401 Unauthorized error.
        """
        url = reverse('token_refresh')
        payload = {
            'refresh': 'invalid.refresh.token'
        }
        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data) # Simple JWT usually includes a detail message
        self.assertIn('code', response.data)   # And an error code like 'token_not_valid'

# Make sure these models are imported at the top
from .models import Profile, Interest, Course, Club, Major, Minor

class ProfileTests(APITestCase):
    """
    Tests for the User Profile endpoint (/api/profile/me/).
    """
    @classmethod
    def setUpTestData(cls):
        """Set up a test user with a profile and related data."""
        cls.User = get_user_model()
        cls.test_username = 'profileuser'
        cls.test_password = 'profilepassword123'
        cls.test_user = cls.User.objects.create_user(
            username=cls.test_username,
            password=cls.test_password,
            email='profile@example.com',
            first_name='Profile',
            last_name='User'
        )
        # Create initial related objects
        cls.major1 = Major.objects.create(name="Initial Major")
        cls.interest1 = Interest.objects.create(name="Initial Interest")
        cls.course1 = Course.objects.create(name="INIT 101")
        cls.club1 = Club.objects.create(name="Initial Club")

        # Create the profile
        cls.profile = Profile.objects.create(
            user=cls.test_user,
            year_in_school=Profile.AcademicYear.JUNIOR,
            department="Initial Department",
            socials={"twitter": "initialuser"}
        )
        # Add initial M2M data
        cls.profile.majors.add(cls.major1)
        cls.profile.interests.add(cls.interest1)
        cls.profile.courses_taking.add(cls.course1)
        cls.profile.clubs.add(cls.club1)

    def _get_access_token(self):
        """Helper method to get an access token for the test user."""
        url = reverse('token_obtain_pair')
        payload = {'email': 'profile@example.com', 'password': self.test_password}
        response = self.client.post(url, payload, format='json')
        
        # For debugging
        if response.status_code != status.HTTP_200_OK:
            print(f"Profile token error: {response.data}")
            
        self.assertEqual(response.status_code, status.HTTP_200_OK, "Failed to get token for profile tests")
        return response.data['access']

    def test_get_profile_me_unauthenticated(self):
        """
        Ensure GET /api/profile/me/ fails without authentication.
        """
        url = reverse('api:profile-me')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_me_authenticated(self):
        """
        Ensure authenticated user can retrieve their profile.
        """
        access_token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        url = reverse('api:profile-me')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check some fields (adjust based on your actual ProfileSerializer if it differs from UpdateSerializer)
        self.assertEqual(response.data['year_in_school'], Profile.AcademicYear.JUNIOR)
        self.assertEqual(response.data['department'], "Initial Department")
        self.assertEqual(response.data['socials'], {"twitter": "initialuser"})
        # Check M2M fields (represented by name due to NameRelatedField)
        self.assertIn("Initial Major", response.data['majors'])
        self.assertIn("Initial Interest", response.data['interests'])
        self.assertIn("INIT 101", response.data['courses_taking'])
        self.assertIn("Initial Club", response.data['clubs'])
        self.assertEqual(len(response.data['majors']), 1) # Ensure only expected items are present

    def test_patch_profile_me_unauthenticated(self):
        """
        Ensure PATCH /api/profile/me/ fails without authentication.
        """
        url = reverse('api:profile-me')
        payload = {'department': 'Updated Department'}
        response = self.client.patch(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_profile_me_authenticated(self):
        """
        Ensure authenticated user can update their profile via PATCH.
        """
        access_token = self._get_access_token()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        url = reverse('api:profile-me')

        # Define updated data - M2M fields require the full desired list
        # because the default DRF update replaces the set.
        update_payload = {
            "department": "Updated Department",
            "year_in_school": Profile.AcademicYear.SENIOR,
            "socials": {"linkedin": "updateduser"},
            "interests": ["Updated Interest", "Hiking"], # Replaces "Initial Interest"
            "majors": ["Updated Major"], # Replaces "Initial Major"
            # courses_taking and clubs will be emptied if not provided
            "courses_taking": ["UPD 202"],
            "clubs": [] # Explicitly empty the clubs list
        }

        response = self.client.patch(url, update_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)

        # Verify the changes in the database
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.department, "Updated Department")
        self.assertEqual(self.profile.year_in_school, Profile.AcademicYear.SENIOR)
        self.assertEqual(self.profile.socials, {"linkedin": "updateduser"})

        # Verify M2M updates
        self.assertEqual(self.profile.interests.count(), 2)
        self.assertTrue(self.profile.interests.filter(name="Updated Interest").exists())
        self.assertTrue(self.profile.interests.filter(name="Hiking").exists())
        self.assertFalse(self.profile.interests.filter(name="Initial Interest").exists()) # Should be gone

        self.assertEqual(self.profile.majors.count(), 1)
        self.assertTrue(self.profile.majors.filter(name="Updated Major").exists())
        self.assertFalse(self.profile.majors.filter(name="Initial Major").exists())

        self.assertEqual(self.profile.courses_taking.count(), 1)
        self.assertTrue(self.profile.courses_taking.filter(name="UPD 202").exists())
        self.assertFalse(self.profile.courses_taking.filter(name="INIT 101").exists())

        self.assertEqual(self.profile.clubs.count(), 0) # Should be empty
        self.assertFalse(self.profile.clubs.filter(name="Initial Club").exists())

    # Todo: Add tests for invalid PATCH data (e.g., bad year_in_school choice) later

class ProfileModelTests(APITestCase):
        """tests for the profile model methods"""
        @classmethod 
        def setUpTestData(cls):
            """ set up data for friendship score calculation"""
            cls.User = get_user_model()
            # Create two test users
            cls.user1 = cls.User.objects.create_user(
                username='user1', 
                password='pass1234',
                email='user1@example.com'
            )
            cls.user2 = cls.User.objects.create_user(
                username='user2', 
                password='pass1234',
                email='user2@example.com'
            )

            # Create profile objects
            cls.profile1 = Profile.objects.create(
                user=cls.user1,
                year_in_school=Profile.AcademicYear.SOPHOMORE,
                department="Computer Science"
            )
            cls.profile2 = Profile.objects.create(
                user=cls.user2,
                year_in_school=Profile.AcademicYear.JUNIOR,
                department="Mathematics"
            )

            # Create personality questions
            questions = [
                PersonalityQuestion.objects.create(text=f"Question {i}", order=i) 
                for i in range(1, 6)
            ]
            
            # Add personality answers for both profiles
            # User 1 answers
            for i, q in enumerate(questions, 1):
                PersonalityAnswer.objects.create(
                    profile=cls.profile1,
                    question=q,
                    answer_score=i  # 1,2,3,4,5
                )

            # User 2 answers - some similar, some different
            scores = [2, 2, 3, 5, 1]  # Mix of similar and different scores
            for i, q in enumerate(questions):
                PersonalityAnswer.objects.create(
                    profile=cls.profile2,
                    question=q,
                    answer_score=scores[i]
                )
                
            

            # Create shared and unique interests/clubs
            cls.interest1 = Interest.objects.create(name="Reading")

            # Mock personality_results for both profiles
            mock_personality_results = [
                {
                    'domain': 'O',
                    'title': 'Openness',
                    'description': 'Openness to experience',
                    'result': 'high',
                    'result_text': 'You are very open to new experiences',
                    'facets': [
                        {'name': 'friendliness', 'score': 16, 'description': 'Tendency to be friendly'},
                        {'name': 'cheerfulness', 'score': 12, 'description': 'Tendency to be cheerful'},
                        {'name': 'sympathy', 'score': 14, 'description': 'Tendency to sympathize'},
                        {'name': 'assertiveness', 'score': 18, 'description': 'Tendency to be assertive'},
                        {'name': 'cooperation', 'score': 10, 'description': 'Tendency to cooperate'},
                        {'name': 'self-efficiency', 'score': 15, 'description': 'Belief in own competence'},
                        {'name': 'anger', 'score': 8, 'description': 'Tendency to experience anger'},
                        {'name': 'modesty', 'score': 11, 'description': 'Tendency to be modest'},
                        {'name': 'self-consciousness', 'score': 9, 'description': 'Ease in social situations'},
                        {'name': 'gregariousness', 'score': 17, 'description': 'Preference for company'},
                        {'name': 'trust', 'score': 13, 'description': 'Tendency to trust others'}
                    ],
                    'raw_score': 32,
                    'count': 10
                }
            ]

            # Patch the personality_results property for both profiles
            cls.profile1.personality_results = mock_personality_results
            cls.profile2.personality_results = mock_personality_results
    
            cls.interest2 = Interest.objects.create(name="Gaming")
            cls.interest3 = Interest.objects.create(name="Hiking")
            cls.club1 = Club.objects.create(name="Chess Club")
            cls.club2 = Club.objects.create(name="Debate Club")
            
            # Add interests and clubs
            cls.profile1.interests.add(cls.interest1, cls.interest2)
            cls.profile2.interests.add(cls.interest1, cls.interest3)
            cls.profile1.clubs.add(cls.club1)
            cls.profile2.clubs.add(cls.club1, cls.club2)


        def test_calculate_friendship_score(self):
            """Test that friendship scores are calculated correctly."""
            # Calculate friendship score
            score = Profile.calculate_friendship_score(self.profile1, self.profile2)
            
            # Verify score is not None
            self.assertIsNotNone(score, "Friendship score should not be None")
            
            # Verify score is a float
            self.assertIsInstance(score, float, "Friendship score should be a float")
            
            # Since we know our test data, we can verify the components too
            rmse_score = Profile.calculate_rmse_score(self.profile1, self.profile2)
            hobby_score = Profile.calculate_hobby_score(self.profile1, self.profile2)
            flag_score = Profile.calculate_flag_score(self.profile1, self.profile2)
            
            # Verify the components are not None
            self.assertIsNotNone(rmse_score, "RMSE score should not be None")
            self.assertIsNotNone(hobby_score, "Hobby score should not be None")
            
            # Verify the result matches the formula
            expected = (rmse_score * 1.5 + flag_score) * (1 + hobby_score/2)
            self.assertAlmostEqual(score, expected, places=5)
            
            # Double-check hobby score calculation
            self.assertEqual(hobby_score, 2/5, "Should have 2 common items (1 interest, 1 club) out of max 5")
            