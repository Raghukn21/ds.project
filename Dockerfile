FROM python:3.9-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Upgrade pip to avoid metadata parsing bugs in older pip versions
RUN pip install --no-cache-dir --upgrade pip

# Install CPU version of PyTorch using extra-index-url so PyPI dependencies can resolve
RUN pip install --no-cache-dir torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# Install remaining dependencies
RUN pip install --default-timeout=1000 --no-cache-dir -r requirements.txt

COPY . .

# Expose the FastAPI port
EXPOSE 8000

# Set Python path
ENV PYTHONPATH=/app

# Command to run the application
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
