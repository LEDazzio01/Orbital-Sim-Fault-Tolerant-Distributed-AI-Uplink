# Ground Station - FastAPI Service (The Client)
FROM python:3.11-slim

WORKDIR /app

COPY src/ ./src/

# Install dependencies (add requirements.txt when ready)
# RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
