# FROM python:3.10-slim

FROM python:3.10-slim-bullseye

WORKDIR /healthChatBot

# Install system deps for psycopg2 + torch
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port
EXPOSE 8000

# Start with gunicorn + uvicorn worker
# … other Dockerfile instructions …

# Use sh -c so $PORT is expanded, with a default of 8000 if PORT isn’t set
CMD ["sh", "-c", "gunicorn -k uvicorn.workers.UvicornWorker main:app --bind=0.0.0.0:${PORT:-8000} --timeout 120"]