# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user
RUN useradd -m -d /home/appuser -s /bin/bash appuser

# Set the working directory in the container
WORKDIR /home/appuser/app

# Create media and static directories and set ownership
RUN mkdir -p media static
RUN chown -R appuser:appuser /home/appuser/app

# Install dependencies
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY --chown=appuser:appuser . .

# Switch to the non-root user
USER appuser

# Expose the port the app runs on
EXPOSE 8000

# Define the command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "file_manager.wsgi:application"]
