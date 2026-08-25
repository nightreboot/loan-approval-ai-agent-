FROM python:3.12-slim

WORKDIR /app

# System dependency (kuch python packages ko chahiye hoti hai)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}