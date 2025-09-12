# Use the official Python image
FROM python:3.10-slim

# Prevent Python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1

# Set the working directory
WORKDIR /app

# System deps for Pillow, psycopg2, etc. + gettext for compilemessages
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
    git \
    libmagic1 \
    gettext \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python3 -m venv /venv

# Copy requirements and install
COPY requirements.txt /app/requirements.txt
RUN /venv/bin/pip install --upgrade pip setuptools wheel
RUN /venv/bin/pip install -r /app/requirements.txt

# Copy project
COPY RhymesOfLife/ /app/RhymesOfLife
COPY RhymesOfLifeShadows/ /app/RhymesOfLifeShadows
COPY environment.json /app

# Compile translations (.po -> .mo)
WORKDIR /app/RhymesOfLife
RUN /venv/bin/python manage.py compilemessages -l ru -l en

# Expose the port
EXPOSE 8000
