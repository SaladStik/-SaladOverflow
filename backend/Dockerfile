FROM python:3.12-slim

WORKDIR /app

# Install system dependencies for MariaDB connector
RUN apt-get update && apt-get install -y \
    libmariadb-dev \
    libmariadb-dev-compat \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "run.py"]
