# Dockerfile for the project, uses slim-bullseye with python 3.11
FROM python:3.11-slim-bullseye

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000