# pull official base image
FROM python:3.11-slim-bookworm

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    netcat-openbsd \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libxcb1 \
    && rm -rf /var/lib/apt/lists/*

# ── Layer 1: Heavy ML deps — cached permanently unless version changes ──
RUN pip install --upgrade pip && \
    pip install \
        deepface==0.0.93 \
        tensorflow==2.19.1 \
        tf-keras==2.19.0

# ── Layer 2: Your project dependencies — rebuilds only when requirements.txt changes ──
COPY ./requirements.txt .
RUN pip install -r requirements.txt

# copy entrypoint
COPY ./entrypoint.sh .
RUN sed -i 's/\r$//g' /usr/src/app/entrypoint.sh
RUN chmod +x /usr/src/app/entrypoint.sh

# ── Layer 3: Your code — rebuilds in seconds ──
COPY . .

# ENTRYPOINT ["/usr/src/app/entrypoint.sh"]