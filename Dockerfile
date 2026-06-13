# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the rest of the application
COPY backend /app/backend/
COPY index.html /app/

# Expose the port
EXPOSE 8000

# Environment variables for production (override in Render dashboard)
ENV JWT_SECRET="bidmont-production-secret-change-me"
ENV ENVIRONMENT="production"

# Run the application from the backend directory
WORKDIR /app/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
