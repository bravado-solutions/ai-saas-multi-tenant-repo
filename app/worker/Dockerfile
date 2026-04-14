FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# The worker shares requirements with the API
# We copy them from the api directory during the build context or root build
COPY ../api/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker source code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

CMD ["python", "worker.py"]