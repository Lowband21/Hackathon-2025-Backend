# Project State Summary (Hackathon 2025 Serendipity Engine Backend)

## Current Status

The backend project is set up using Dockerized Django, PostgreSQL, and Gunicorn. The core functionality implemented includes:

1.  **User Authentication:**
    *   Uses `djangorestframework-simplejwt` for JWT-based authentication.
    *   Endpoints `/api/auth/token/` (obtain token pair) and `/api/auth/token/refresh/` (refresh access token) are configured.
    *   A `CustomUser` model extending Django's `AbstractUser` is defined and configured (`AUTH_USER_MODEL`).

2.  **User Onboarding:**
    *   Endpoint `POST /api/onboarding/` allows new user registration.
    *   Collects basic user info (`username`, `email`, `password`, names), profile details (`year_in_school`, `department`, `socials`), related entities (`majors`, `minors`, `interests`, `courses_taking`, `favorite_courses`, `clubs`), and personality quiz answers.
    *   Creates the `CustomUser` and associated `Profile` instance, linking all related data.

3.  **Profile Management:**
    *   Endpoint `GET /api/profile/me/` allows an authenticated user to retrieve their profile details.
    *   Endpoint `PATCH /api/profile/me/` allows an authenticated user to update their profile details (majors, minors, interests, courses, clubs, socials, etc.).
    *   Uses the `Profile` model linked one-to-one with `CustomUser`.

4.  **Personality Quiz:**
    *   Endpoint `GET /api/personality-questions/` lists available questions.
    *   Models `PersonalityQuestion` and `PersonalityAnswer` are defined to store questions and user responses linked to their profile.
    *   Answers are submitted during onboarding via the `POST /api/onboarding/` endpoint.

5.  **API Testing:**
    *   Automated tests using Django REST Framework's `APITestCase` have been implemented in `backend/api/tests.py`.
    *   Current tests cover the primary success ("happy path") scenarios and basic failure conditions (authentication/authorization) for the onboarding, authentication (JWT obtain/refresh), profile management (GET/PATCH), and personality question listing endpoints.
    *   Further tests covering edge cases and various invalid input scenarios can be added for increased robustness.

## Project Structure (`backend` directory)

```
backend/
├── api/                  # Main application logic
│   ├── migrations/       # Database migration files for the api app
│   ├── __init__.py
│   ├── admin.py          # Django admin configurations (currently basic)
│   ├── apps.py           # App configuration
│   ├── models.py         # Defines database tables (CustomUser, Profile, Interest, etc.)
│   ├── serializers.py    # Defines data validation and representation (Onboarding, ProfileUpdate, etc.)
│   ├── tests.py          # Automated API tests using APITestCase
│   ├── urls.py           # URL routing specific to the 'api' app (/onboarding/, /profile/me/, etc.)
│   └── views.py          # Handles request/response logic (OnboardingView, UserProfileView, etc.)
├── core/                 # Django project configuration
│   ├── __init__.py
│   ├── asgi.py           # ASGI config for async support (not primary focus)
│   ├── settings.py       # Project-wide settings (DB, installed apps, auth, JWT, etc.)
│   ├── urls.py           # Root URL configuration (routes to admin, api app, auth endpoints)
│   └── wsgi.py           # WSGI config for synchronous servers like Gunicorn
├── manage.py             # Django's command-line utility
└── requirements.txt      # Python package dependencies (Django, DRF, psycopg2, JWT, etc.)

Other Files:
├── Dockerfile            # Instructions to build the backend Docker image
├── docker-compose.yml    # Defines services (backend, db) and their configuration
├── .env.example          # Example environment variables
├── .env                  # Actual environment variables (DB credentials, SECRET_KEY - *ignored by git*)
├── README.md             # Project overview and setup instructions
└── project_state.md      # This file
```

## Interdependencies

*   **`docker-compose.yml` / `Dockerfile`:** Define the runtime environment. `Dockerfile` uses `requirements.txt` to install dependencies. `docker-compose.yml` links the `backend` service to the `db` service and uses `.env` for environment variables (like database credentials).
*   **`.env`:** Provides sensitive settings (database credentials, `SECRET_KEY`, `DEBUG` status, `ALLOWED_HOSTS`) to `settings.py`.
*   **`backend/core/settings.py`:**
    *   Reads `.env`.
    *   Defines `INSTALLED_APPS` (includes `rest_framework`, `rest_framework_simplejwt`, `api`).
    *   Configures `DATABASES` using env vars.
    *   Sets `AUTH_USER_MODEL = 'api.CustomUser'`.
    *   Configures `REST_FRAMEWORK` (default authentication to `JWTAuthentication`, default permissions).
    *   Configures `SIMPLE_JWT` settings (token lifetimes, signing key uses `SECRET_KEY`).
    *   Specifies `ROOT_URLCONF = 'core.urls'`.
*   **`backend/core/urls.py`:**
    *   Imports `include` to route `/api/` to `api.urls`.
    *   Imports and configures Simple JWT's `TokenObtainPairView` and `TokenRefreshView` at `/api/auth/token/` and `/api/auth/token/refresh/`.
*   **`backend/api/urls.py`:**
    *   Defines specific API endpoints (`/onboarding/`, `/profile/me/`, `/personality-questions/`).
    *   Maps these paths to views defined in `api/views.py`.
*   **`backend/api/views.py`:**
    *   Imports `generics` and `permissions` from `rest_framework`.
    *   Imports models (`Profile`, `PersonalityQuestion`, `User`) from `api/models.py`.
    *   Imports serializers (`OnboardingSerializer`, `ProfileUpdateSerializer`, `PersonalityQuestionSerializer`) from `api/serializers.py`.
    *   Defines view logic, linking serializers, querysets (models), and permission classes (`AllowAny`, `IsAuthenticated`).
    *   `UserProfileView` uses `request.user` (provided by JWT authentication middleware) to fetch the correct profile.
*   **`backend/api/serializers.py`:**
    *   Imports `serializers` from `rest_framework`.
    *   Imports all relevant models from `api/models.py`.
    *   Imports `get_user_model` to reference the `CustomUser`.
    *   Defines how model data is converted to/from JSON.
    *   `OnboardingSerializer` contains complex logic for creating `User`, `Profile`, and related `PersonalityAnswer` instances within a transaction. Includes nested serializers and custom `NameRelatedField` for handling M2M relationships by name. (Note: `source` attribute removed from profile fields as logic is handled in `create`).
    *   `ProfileUpdateSerializer` handles partial updates to the `Profile` model.
*   **`backend/api/models.py`:**
    *   Defines the database schema using Django's ORM (`models.Model`).
    *   `CustomUser` extends `AbstractUser`.
    *   `Profile` has a `OneToOneField` to `settings.AUTH_USER_MODEL` and `ManyToManyField` to `Interest`, `Course`, `Club`, `Major`, `Minor`.
    *   Relationships (`ForeignKey`, `ManyToManyField`) define how tables are linked.
    *   Uses `settings.AUTH_USER_MODEL` to correctly link to the active user model.
*   **`backend/manage.py`:** Uses `settings.py` to configure Django for management commands (like `runserver`, `makemigrations`, `migrate`).
*   **`backend/requirements.txt`:** Lists all Python dependencies required by the project, installed via `pip` (usually within the Docker build process).
*   **`backend/api/tests.py`:** Contains `APITestCase` tests for core API endpoints. Relies on URL names defined in `api/urls.py` and `core/urls.py`, interacts with views/serializers, and asserts database state changes based on models in `api/models.py`.