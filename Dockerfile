# Use Python image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy the requirements.txt and install dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Set the environment variable for Flask
ENV FLASK_APP=main.py

# Expose port 5000
EXPOSE 5000

# Command to run the application
CMD ["python3", "main.py"]
