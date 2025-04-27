# backend/api/management/commands/generate_test_users.py
import random
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from api.models import (
    Profile, Interest, Course, Club, Major, Minor,
    PersonalityQuestion, PersonalityAnswer
)

User = get_user_model()

class Command(BaseCommand):
    help = 'Generate test users with profiles, interests, courses, and personality answers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of test users to create (default: 10)'
        )
        parser.add_argument(
            '--purge',
            action='store_true',
            help='Delete existing test users before creating new ones'
        )

    def handle(self, *args, **options):
        count = options['count']
        purge = options.get('purge', False)
        
        # Sample data for test users
        MAJORS = ["Computer Science", "Psychology", "Biology", "Economics", 
                "Mathematics", "English", "Political Science", "Physics", 
                "History", "Chemistry", "Mechanical Engineering"]
        
        MINORS = ["Data Science", "Business", "Statistics", "Creative Writing", 
                "Music", "Art History", "Spanish", "French", "Environmental Studies", 
                "Philosophy", "Film Studies"]
        
        INTERESTS = ["Programming", "Reading", "Hiking", "Gaming", "Music", 
                    "Sports", "Photography", "Cooking", "Travel", "Movies", 
                    "Art", "Dancing", "Chess", "Yoga", "Writing"]
        
        COURSES = [
            {"name": "Intro to Computer Science", "department": "COMP", "course_number": "101"},
            {"name": "Data Structures", "department": "COMP", "course_number": "201"},
            {"name": "Algorithms", "department": "COMP", "course_number": "301"},
            {"name": "Machine Learning", "department": "COMP", "course_number": "401"},
            {"name": "General Psychology", "department": "PSYC", "course_number": "101"},
            {"name": "Cognitive Psychology", "department": "PSYC", "course_number": "301"},
            {"name": "Intro to Biology", "department": "BIO", "course_number": "101"},
            {"name": "Microeconomics", "department": "ECON", "course_number": "101"},
            {"name": "Macroeconomics", "department": "ECON", "course_number": "201"},
            {"name": "Calculus I", "department": "MATH", "course_number": "101"},
            {"name": "Calculus II", "department": "MATH", "course_number": "102"},
            {"name": "Literature & Composition", "department": "ENG", "course_number": "101"},
            {"name": "Physics I", "department": "PHYS", "course_number": "101"},
            {"name": "U.S. History", "department": "HIST", "course_number": "101"},
            {"name": "Organic Chemistry", "department": "CHEM", "course_number": "201"}
        ]
        
        CLUBS = ["Coding Club", "Chess Club", "Debate Team", "Hiking Club", 
                "Photography Club", "Theatre Group", "Student Government", 
                "Robotics Team", "Environmental Club", "Film Society", 
                "Music Society", "Dance Club", "Art Club", "Book Club"]
        
        # First names and last names for generating realistic usernames
        FIRST_NAMES = ["Alex", "Jamie", "Jordan", "Taylor", "Morgan", "Casey", 
                      "Riley", "Avery", "Quinn", "Dakota", "Skyler", "Charlie",
                      "Blake", "Cameron", "Hayden", "Drew", "Alexis", "Parker",
                      "Reese", "Bailey", "Sam", "Rowan", "Jesse", "Phoenix"]
        
        LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", 
                     "Miller", "Davis", "Rodriguez", "Martinez", "Hernandez", 
                     "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", 
                     "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", 
                     "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez"]
        
        # Academic years
        ACADEMIC_YEARS = [year[0] for year in Profile.AcademicYear.choices]
        
        # Create or get personality questions
        if not PersonalityQuestion.objects.exists():
            self.stdout.write("Creating personality questions...")
            questions = [
                {"text": "I enjoy meeting new people", "domain": "E", "facet": "1", "order": 1},
                {"text": "I prefer a structured routine", "domain": "C", "facet": "2", "order": 2},
                {"text": "I often worry about things", "domain": "N", "facet": "1", "order": 3},
                {"text": "I am interested in abstract ideas", "domain": "O", "facet": "5", "order": 4},
                {"text": "I sympathize with others' feelings", "domain": "A", "facet": "3", "order": 5},
                {"text": "I enjoy working in teams", "domain": "E", "facet": "2", "order": 6},
                {"text": "I set high standards for myself", "domain": "C", "facet": "4", "order": 7},
                {"text": "I handle stress well", "domain": "N", "facet": "2", "reverse_scale": True, "order": 8},
                {"text": "I enjoy creative activities", "domain": "O", "facet": "1", "order": 9},
                {"text": "I value harmony in my relationships", "domain": "A", "facet": "4", "order": 10},
            ]
            
            for q_data in questions:
                PersonalityQuestion.objects.get_or_create(
                    text=q_data["text"],
                    defaults={
                        "domain": q_data["domain"],
                        "facet": q_data.get("facet", "1"),
                        "reverse_scale": q_data.get("reverse_scale", False),
                        "order": q_data["order"]
                    }
                )
        
        # Create reference data (majors, minors, interests, courses, clubs)
        self.stdout.write("Creating reference data...")
        created_majors = []
        for major_name in MAJORS:
            major, _ = Major.objects.get_or_create(name=major_name)
            created_majors.append(major)
            
        created_minors = []
        for minor_name in MINORS:
            minor, _ = Minor.objects.get_or_create(name=minor_name)
            created_minors.append(minor)
            
        created_interests = []
        for interest_name in INTERESTS:
            interest, _ = Interest.objects.get_or_create(name=interest_name)
            created_interests.append(interest)
            
        created_courses = []
        for course_data in COURSES:
            course, _ = Course.objects.get_or_create(
                name=course_data["name"],
                department=course_data["department"],
                course_number=course_data["course_number"]
            )
            created_courses.append(course)
            
        created_clubs = []
        for club_name in CLUBS:
            club, _ = Club.objects.get_or_create(name=club_name)
            created_clubs.append(club)
        
        # Get all personality questions
        personality_questions = list(PersonalityQuestion.objects.all())
        
        # Purge existing test users if requested
        if purge:
            self.stdout.write("Purging existing test users...")
            User.objects.filter(email__endswith='@testuser.com').delete()
        
        # Create test users
        self.stdout.write(f"Creating {count} test users...")
        created_count = 0
        
        with transaction.atomic():
            for i in range(count):
                # Generate a unique email and username
                first_name = random.choice(FIRST_NAMES)
                last_name = random.choice(LAST_NAMES)
                email = f"{first_name.lower()}.{last_name.lower()}{i}@testuser.com"
                
                # Create basic user
                user = User.objects.create_user(
                    email=email,
                    password="testpassword",  # Simple password for all test users
                    first_name=first_name,
                    last_name=last_name,
                    preferred_name=first_name if random.random() > 0.7 else ""
                )
                
                # Create profile
                profile = Profile.objects.create(
                    user=user,
                    year_in_school=random.choice(ACADEMIC_YEARS),
                    department=random.choice(created_majors).name if random.random() > 0.5 else "",
                    socials={
                        "instagram": f"{first_name.lower()}{last_name.lower()}" if random.random() > 0.4 else "",
                        "snapchat": f"{first_name.lower()}.snap" if random.random() > 0.6 else "",
                        "x": f"@{first_name.lower()}{random.randint(10, 999)}" if random.random() > 0.7 else ""
                    }
                )
                
                # Add random majors (1-2)
                num_majors = random.randint(1, 2)
                profile.majors.set(random.sample(created_majors, num_majors))
                
                # Add random minors (0-2)
                num_minors = random.randint(0, 2)
                profile.minors.set(random.sample(created_minors, num_minors))
                
                # Add random interests (3-7)
                num_interests = random.randint(3, 7)
                profile.interests.set(random.sample(created_interests, num_interests))
                
                # Add random courses (3-6)
                num_courses = random.randint(3, 6)
                selected_courses = random.sample(created_courses, num_courses)
                profile.courses_taking.set(selected_courses)
                
                # Add random favorite courses (1-3) from the courses they're taking
                num_favs = random.randint(1, min(3, len(selected_courses)))
                profile.favorite_courses.set(random.sample(selected_courses, num_favs))
                
                # Add random clubs (0-3)
                num_clubs = random.randint(0, 3)
                profile.clubs.set(random.sample(created_clubs, num_clubs))
                
                # Create personality answers
                answers_to_create = []
                for question in personality_questions:
                    answers_to_create.append(
                        PersonalityAnswer(
                            profile=profile,
                            question=question,
                            answer_score=random.randint(1, 5)
                        )
                    )
                PersonalityAnswer.objects.bulk_create(answers_to_create)
                
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {created_count} test users'))
        
        # Display login credentials for created users
        self.stdout.write("\nGenerated Test Users:")
        self.stdout.write("=====================")
        self.stdout.write("Email                         | Password")
        self.stdout.write("------------------------------|----------")
        
        for user in User.objects.filter(email__endswith='@testuser.com').order_by('email'):
            self.stdout.write(f"{user.email:<30} | testpassword")
            
        self.stdout.write("\nAll users have the password: 'testpassword'")