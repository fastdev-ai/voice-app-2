FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY templates templates/

# Create recordings directory
RUN mkdir -p recordings

# Default environment variables (can be overridden at runtime)
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=5001 \
    HOST=0.0.0.0 \
    FLASK_DEBUG=false \
    UPLOAD_FOLDER=/app/recordings \
    COST_PER_MINUTE=0.006 \
    CONFIRM_DELETE=false \
    TITLE="Voice Input"

# Expose port (note: actual port used will be from the PORT env var)
EXPOSE 5001

# Run the application
CMD ["python", "app.py"]
