FROM python:3.10-slim-buster

WORKDIR /app

# Copy files from my local directory (where this Dockerfile is) into the image, which is relative to WORKDIR
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Needed to make sure the prints work
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Run the app
CMD ["python3", "k8_app.py"]
