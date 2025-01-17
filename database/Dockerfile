# Use the official Python image as the base image
FROM python:3.12-slim


WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . /app/

# Expose FastAPI's port
EXPOSE 8000

# Run FastAPI application using Uvicorn
CMD ["uvicorn", "app.data_service:app", "--host", "0.0.0.0", "--port", "8000"]
