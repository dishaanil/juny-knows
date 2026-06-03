FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend + frontend
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Cloud Run injects PORT — default to 8080
ENV PORT=8080

WORKDIR /app/backend

CMD uvicorn main:app --host 0.0.0.0 --port $PORT
