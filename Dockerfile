# Dockerfile

# --- Base Stage ---
# Use an official Python runtime as a parent image
FROM python:3.10-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1 # Prevents python from writing pyc files
ENV PYTHONUNBUFFERED 1       # Prevents python from buffering stdout/stderr

# Set work directory
WORKDIR /app

# Install system dependencies (if needed, e.g., for psycopg2 non-binary)
# RUN apt-get update && apt-get install -y --no-install-recommends \
#    build-essential libpq-dev \
#    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ./backend/requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Development Stage ---
FROM base as development

# Copy project code
# Note: We copy requirements again in case they changed
COPY ./backend/requirements.txt /app/requirements.txt
COPY ./backend /app/

# Expose port (Gunicorn will run on this port)
EXPOSE 8000

# Default command (can be overridden in docker-compose)
# Run gunicorn - use --reload for development
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--worker-class", "gthread", "core.wsgi:application", "--reload"]


# --- Production Stage (Example - you might refine this later) ---
FROM base as production

# Copy only necessary code and installed dependencies from base
COPY --from=base /app /app
COPY ./backend /app/

# Expose port
EXPOSE 8000

# Run Gunicorn (no reload, more workers typically)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "core.wsgi:application"]
