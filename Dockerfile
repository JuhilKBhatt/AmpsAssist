# ./Dockerfile
FROM python:3.12-slim

# Install ffmpeg (required by yt-dlp to convert to mp3)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create a volume mount point for the downloads
VOLUME ["/app/downloads"]

# Run the application
CMD ["python", "src/main.py"]