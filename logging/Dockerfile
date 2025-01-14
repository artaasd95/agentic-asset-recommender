# Use a lightweight Python image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only requirements to leverage Docker's cache
COPY app/requirements.txt /app/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the application code
COPY app /app

# Expose the port FastAPI will run on
EXPOSE 8000

# Command to run FastAPI via Uvicorn
CMD ["uvicorn", "logging_service:app", "--host", "0.0.0.0", "--port", "8000"]
