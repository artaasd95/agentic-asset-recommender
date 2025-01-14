# Dockerfile
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy requirements first, for efficient builds (layer caching)
COPY requirements.txt /app/

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app/

# Expose the port
EXPOSE 8000

# Run FastAPI via Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
