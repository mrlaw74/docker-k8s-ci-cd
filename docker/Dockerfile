FROM python:3.11-slim

WORKDIR /app

# Copy configuration files
COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/ .
COPY public/ ./public/

EXPOSE 5000

CMD ["python", "app.py"]
