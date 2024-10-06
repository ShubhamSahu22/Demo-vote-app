# Define the base stage that uses the official Python runtime base image
FROM python:3.11-slim AS base

# Add curl for healthcheck and clean up afterwards
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory for the application                        
WORKDIR /usr/local/app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Define the development stage with additional dev-specific tools
FROM base AS dev

# Install watchdog to monitor filesystem changes
RUN pip install watchdog

# Set environment variable for development mode
ENV FLASK_ENV=development

# Command to run in development mode
CMD ["python", "app.py"]

# Define the final production stage
FROM base AS final

# Copy application code from the current directory to the working directory in the container
COPY . .

# Expose port 80 for web traffic
EXPOSE 80

# Command to run in production using gunicorn with 4 workers
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:80", "--log-file", "-", "--access-logfile", "-", "--workers", "4", "--keep-alive", "0"]
