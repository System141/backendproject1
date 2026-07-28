# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first for layer caching
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy the rest of the application
COPY backend /app/backend/
COPY index.html /app/index.html

# Expose the port
EXPOSE 8000

# Environment variables for production (override at container runtime)
# WARNING: JWT_SECRET must be supplied via runtime environment — never hardcode secrets!
ENV ENVIRONMENT="production"
ENV CORS_ORIGINS=""

# Run the application from the backend directory
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
