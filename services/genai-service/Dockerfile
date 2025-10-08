# Stage 1: The builder stage with build-time dependencies
FROM python:3.12-slim as builder

# Install system dependencies needed for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Set up a virtual environment
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---

# Stage 2: The final, lightweight runtime image
FROM python:3.12-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code
COPY . .

# Activate the virtual environment
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Expose the correct port for Azure App Service
EXPOSE 8080

# Run the application on the correct port and ensure the path matches your project
# (Use "app.main:app" if your main.py is inside an 'app' folder)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]