# Dockerfile for the project, uses slim-bullseye with python 3.11
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Update system packages and install security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install build-essential for compiling packages
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install build-essential -y && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get -y install wget curl gnupg && \
    rm -rf /var/lib/apt/lists/*

# Add NVIDIA package repositories
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb && \
    dpkg -i cuda-keyring_1.1-1_all.deb && \
    apt-get update && apt-get install -y cuda-toolkit-12-9 && \
    rm -rf /var/lib/apt/lists/*

ENV PATH=${PATH}:/usr/local/cuda/bin
ENV LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/local/cuda/lib64

# Set the working directory
WORKDIR /app

# Start the project with uv
# RUN uv sync --locked
ENV UV_SYSTEM_PYTHON=1

# Copy the current directory contents into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt with uv instead of pip 
RUN uv pip install -r requirements.txt

# Create a user to run the application with default id and group
RUN groupadd -r appgrp -g 1000
RUN useradd -u 1000 -g appgrp -s /bin/bash appuser
RUN mkdir /home/appuser
RUN chown -R appuser /home/appuser
RUN chown -R appuser /app
USER appuser


EXPOSE 8000