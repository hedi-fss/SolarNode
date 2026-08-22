FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/data /app/logs

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir "numpy==1.26.4" && \
    pip install --no-cache-dir scipy scikit-learn --force-reinstall

COPY . .

RUN chmod -R 755 /app/data /app/logs

ENV PORT=5001
EXPOSE 5001

CMD ["python", "run.py"]
