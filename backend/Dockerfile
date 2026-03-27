FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code into /app/backend/ so `backend.*` imports work
COPY . ./backend/

# Make /app the Python path root
ENV PYTHONPATH=/app

# Run uvicorn on port 8000
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
