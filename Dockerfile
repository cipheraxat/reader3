FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create books directory
RUN mkdir -p /app/books

# Expose port
EXPOSE 8123

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV BOOKS_DIR=/app
ENV HOST=0.0.0.0
ENV PORT=8123

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8123/health')"

# Run the application
CMD ["python", "server.py"]
