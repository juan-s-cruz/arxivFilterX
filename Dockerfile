# Dockerfile for the project, uses slim-bullseye with python 3.11
FROM python:3.11-slim-bullseye

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Create a user to run the application with default id and group
RUN groupadd -r appgrp -g 1000
RUN useradd -u 1000 -g appgrp -s /bin/bash appuser
RUN chown -R appuser /app
USER appuser

EXPOSE 8000