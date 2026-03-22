# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container at /app
COPY . /app/

# Create instance directory for SQLite database
RUN mkdir -p /app/instance

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose port 5050 for the Flask application
EXPOSE 5050

# Set the entrypoint to run migrations and start the server
ENTRYPOINT ["/app/entrypoint.sh"]
