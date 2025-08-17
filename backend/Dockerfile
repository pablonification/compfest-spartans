FROM python:3.13-slim

# Install system dependencies (optional, for building future packages)
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential \
  && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project metadata first (leveraging docker layer cache)
COPY pyproject.toml /app/

# Install Python dependencies from pyproject.toml
RUN pip install --no-cache-dir "fastapi>=0.116.1" "uvicorn[standard]>=0.35.0" "motor>=3.3.1" "python-dotenv>=1.0.1" "requests>=2.31.0" "opencv-python-headless>=4.10.0" "numpy>=1.26" "Pillow>=10.3.0" "python-multipart>=0.0.6" "websockets>=12.0" "httpx>=0.27.0" "google-auth>=2.23.4" "google-auth-oauthlib>=1.1.0" "python-jose[cryptography]>=3.3.0" "pydantic>=2.11.7"

# Copy source code
COPY src /app/src

# Expose API port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
