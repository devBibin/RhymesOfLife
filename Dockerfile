# Use the official Python image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Install system dependencies required for cffi, Pillow, and other Python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libpq-dev \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libtiff-dev \
    libopenjp2-7-dev \
    libpng-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3 -m venv /venv

# Copy requirements.txt into the container
COPY requirements.txt /app/requirements.txt

# Upgrade pip, setuptools, and wheel
RUN /venv/bin/pip install --upgrade pip setuptools wheel

# Install Python dependencies from requirements.txt
RUN /venv/bin/pip install -r /app/requirements.txt

# Copy the application code into the container
COPY RhymesOfLife/ /app/RhymesOfLife
#COPY IG_Commenter_shadows/ /app/IG_Commenter_shadows
#COPY IG_Dashboard_shadows/ /app/IG_Dashboard_shadows
COPY environment.json /app


# Set the working directory to the Django project folder
WORKDIR /app/RhymesOfLife

# Expose the port Django runs on
EXPOSE 8000
