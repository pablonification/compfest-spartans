FROM python:3.11-slim

# Install system dependencies (optional, for building future packages)
# system libs for OpenCV (libGL) and others
RUN apt-get update \
  && apt-get install -y --no-install-recommends build-essential libgl1 libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy project metadata first (leveraging docker layer cache)
COPY pyproject.toml /app/

# Install Python dependencies (minimal for now; extended deps will be added later)
RUN pip install --no-cache-dir "fastapi>=0.116.1" "uvicorn[standard]>=0.35.0" motor redis python-dotenv requests httpx opencv-python-headless numpy Pillow python-multipart websockets PyJWT python-jose[cryptography] pytest pytest-asyncio inference-sdk

# Copy source code
COPY src /app/src

# Expose API port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
