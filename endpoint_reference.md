# API Endpoint Reference

This document details the available API endpoints for the Serendipity Engine backend.

## Authentication (JWT)

Base Path: `/api/auth/`

These endpoints handle user authentication using JSON Web Tokens (JWT).

### 1. Obtain Token Pair

*   **Endpoint:** `POST /api/auth/token/`
*   **Description:** Authenticates a user with their credentials and returns a pair of JWT tokens (access and refresh).
*   **Permissions:** `AllowAny`
*   **Request Body:**
    ```json
    {
        "email": "user@example.com", // Or username if configured differently
        "password": "yourpassword"
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```
*   **Failure Response (401 Unauthorized):** If credentials are invalid.

### 2. Refresh Access Token

*   **Endpoint:** `POST /api/auth/token/refresh/`
*   **Description:** Obtains a new access token using a valid refresh token.
*   **Permissions:** `AllowAny` (but requires a valid refresh token)
*   **Request Body:**
    ```json
    {
        "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // User's current refresh token
    }
    ```
*   **Success Response (200 OK):**
    ```json
    {
        "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // New access token
    }
    ```
*   **Failure Response (401 Unauthorized):** If the refresh token is invalid or expired.

## Application API

Base Path: `/api/`

These endpoints handle the core application logic like user onboarding and profile management.

### 3. User Onboarding

*   **Endpoint:** `POST /api/onboarding/`
*   **Description:** Registers a new user, creates their associated profile, and records their initial personality quiz answers. This is a single atomic transaction.
*   **Permissions:** `AllowAny`
*   **Request Body:**
    ```json
    {
        "email": "newuser@example.com",
        "password": "strongpassword",
        "first_name": "Test", // Optional
        "last_name": "User", // Optional
        "preferred_name": "Tester", // Optional
        "image": "(binary image data)", // Optional - multipart/form-data upload
        "year_in_school": "SO", // Optional - See Profile.AcademicYear choices
        "department": "Computer Science", // Optional
        "socials": { // Optional - Freeform JSON
            "linkedin": "linkedin.com/in/testuser",
            "github": "github.com/testuser"
        },
        "majors": ["Computer Science", "Mathematics"], // Optional - List of major names (strings)
        "minors": ["Physics"], // Optional - List of minor names (strings)
        "interests": ["Board Games", "Hiking", "Python"], // Optional - List of interest names (strings)
        "courses_taking": ["COMP 2800", "MATH 3100"], // Optional - List of course names/identifiers (strings)
        "favorite_courses": ["COMP 1800"], // Optional - List of course names/identifiers (strings)
        "clubs": ["Coding Club", "Board Game Club"], // Optional - List of club names (strings)
        "personality_answers": [ // Required - List of answers
            {
                "question_id": 1, // ID of the PersonalityQuestion
                "answer_score": 4 // Integer score (1-5)
            },
            {
                "question_id": 2,
                "answer_score": 2
            }
            // ... include answers for all required questions
        ]
    }
    ```
    *Note: For `image` upload, use `multipart/form-data` content type.*
    *Note: Related items (majors, minors, interests, courses, clubs) are looked up or created based on their `name`.*
*   **Success Response (201 Created):** Returns the created user data (excluding sensitive fields like password, including profile fields).
*   **Failure Response (400 Bad Request):** If validation fails (e.g., missing required fields, invalid email, invalid `question_id`, score out of range).

### 4. User Profile Management

*   **Endpoint:** `/api/profile/me/`
*   **Permissions:** `IsAuthenticated` (Requires valid JWT access token in `Authorization: Bearer <token>` header)
*   **Methods:**
    *   **`GET`**
        *   **Description:** Retrieves the profile details of the currently authenticated user.
        *   **Success Response (200 OK):** Returns the user's profile data using the `ProfileUpdateSerializer` structure (see PATCH below for fields).
    *   **`PATCH`**
        *   **Description:** Partially updates the profile details of the currently authenticated user. Only include fields to be updated.
        *   **Request Body:** (Example - updating interests and department)
            ```json
            {
                "department": "Electrical Engineering",
                "interests": ["Robotics", "Hiking", "Embedded Systems"] // Replaces the entire list of interests
            }
            ```
        *   **Accepted Fields for Update:** `image`, `year_in_school`, `department`, `socials`, `majors`, `minors`, `interests`, `courses_taking`, `favorite_courses`, `clubs`.
        *   *Note: For M2M fields (majors, minors, etc.), providing a list will **replace** the existing set.*
        *   *Note: For `image` update, use `multipart/form-data`.*
        *   **Success Response (200 OK):** Returns the updated profile data.
        *   **Failure Response (400 Bad Request):** If validation fails.

### 5. List Personality Questions

*   **Endpoint:** `GET /api/personality-questions/`
*   **Description:** Retrieves a list of all available personality questions, ordered by their `order` field.
*   **Permissions:** `AllowAny`
*   **Success Response (200 OK):**
    ```json
    [
        {
            "id": 1,
            "text": "Question text 1...",
            "order": 1
        },
        {
            "id": 2,
            "text": "Question text 2...",
            "order": 2
        }
        // ... other questions
    ]