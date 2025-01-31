FROM python:3.12-slim

# Install system dependencies (including a C compiler)
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN mkdir query_translator

COPY . /app/query_translator

WORKDIR /app/query_translator

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app/


EXPOSE 5000


CMD ["python", "-m", "query_translator.main"]
