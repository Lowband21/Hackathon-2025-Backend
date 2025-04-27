# Hackathon 2025 Serendipity Engine Backend

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) Brief description of the project: Fostering unexpected positive interactions on campus by connecting opt-in users based on shared general location and interests/skills/courses. Built for 2025 DU Hackathon.

**Current Status:** [Initial Setup Complete]

## Concept

Moves beyond planned meetings to engineer serendipity. Focuses on shared context (location + interest) for spontaneous connection.

## Tech Stack

* **Backend:** Python / Django / Django REST Framework
* **Database:** PostgreSQL
* **Server:** Gunicorn
* **Containerization:** Docker / Docker Compose

## Project Setup

Follow these steps to get the development environment running locally using Docker.

**Prerequisites:**

* [Git](https://git-scm.com/)
* [Docker](https://www.docker.com/products/docker-desktop/)
* [Docker Compose](https://docs.docker.com/compose/install/) (Usually included with Docker Desktop)

**Steps:**

1.  **Clone the repository:**
    ```bash
    git clone git@github.com:Lowband21/Hackathon-2025-Backend.git
    cd Hackathon-2025-Backend
    ```

2.  **Create Environment File:**
    Copy the example environment file and fill in your secrets and settings. **This file is ignored by git and should NEVER be committed.**
    ```bash
    cp .env.example .env
    ```

3.  **Build and Run Docker Containers:**
    This command builds the Docker images (if they don't exist or `requirements.txt`/`Dockerfile` changed) and starts the services (backend app, database) in the background.
    ```bash
    docker-compose build
    docker-compose up -d
    ```

4.  **Apply Database Migrations:**
    Run the initial Django database migrations to set up the necessary tables.
    ```bash
    docker-compose exec backend python manage.py migrate
    ```

5.  **Create Superuser (Optional):**
    To access the Django admin interface (`/admin/`), create a superuser.
    ```bash
    docker-compose exec backend python manage.py createsuperuser
    ```
    Follow the prompts to set a username, email, and password.

6.  **Access the Application:**
    The Django development server (run via Gunicorn inside Docker) should now be accessible at:
    * Backend API: [http://localhost:8000/](http://localhost:8000/) (or specific API endpoints like `http://localhost:8000/api/`)
    * Django Admin: [http://localhost:8000/admin/](http://localhost:8000/admin/)

## Development Workflow

* **Making Code Changes:** The `backend` directory is mounted as a volume into the `backend` container. Gunicorn is run with `--reload`, so changes to Python files should automatically restart the server within the container.
* **Running Management Commands:** Use `docker-compose exec backend python manage.py <command>`. Examples:
    * `docker-compose exec backend python manage.py makemigrations` (after changing models)
    * `docker-compose exec backend python manage.py migrate`
    * `docker-compose exec backend python manage.py shell` (to open a Django shell)
* **Adding/Updating Dependencies:**
    1.  Add/change packages in `backend/requirements.txt`.
    2.  Rebuild the backend image: `docker-compose build backend`
    3.  Restart the service: `docker-compose up -d --force-recreate backend`
* **Running Tests:**
    ```bash
    docker-compose exec backend python manage.py test
    ```
* **Stopping Containers:**
    ```bash
    docker-compose down # Stops and removes containers
    ```
    To stop and remove the data volume (use with caution!):
    ```bash
    docker-compose down -v
    ```
* **Linting/Formatting:** [Mention any tools used, e.g., Black, Flake8, and how to run them, perhaps via docker-compose exec]

## API Endpoints

The core API endpoints are:

*   `POST /api/auth/token/`: Obtain JWT access and refresh tokens using email/password.
*   `POST /api/auth/token/refresh/`: Refresh JWT access token using a refresh token.
*   `POST /api/onboarding/`: Register a new user, create their profile, and submit initial personality answers.
*   `GET /api/profile/me/`: Retrieve the authenticated user's profile.
*   `PATCH /api/profile/me/`: Update the authenticated user's profile.
*   `GET /api/personality-questions/`: List available personality questions for the quiz.

For detailed request/response formats and required fields, see `endpoint_reference.md`.

## Privacy Considerations

This project handles potentially sensitive user location and interest data. Key privacy principles include:
* Strictly opt-in participation.
* Data minimization - only store what's necessary.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
