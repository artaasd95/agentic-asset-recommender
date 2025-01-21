FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    build-essential \
    libffi-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install the Python dependencies
COPY requirements.txt /app/requirements.txt
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose the port
EXPOSE 8000

# Run FastAPI via Uvicorn
CMD ["uvicorn", "app.chat:app", "--host", "0.0.0.0", "--port", "8000"]
