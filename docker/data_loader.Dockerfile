FROM python:3.10-slim

WORKDIR /app

RUN pip install --no-cache-dir pandas psycopg2-binary

COPY init_postgres/load_data.py /app/load_data.py

CMD ["python", "/app/load_data.py"]
