FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -c "\
import fastapi, uvicorn, pydantic, aio_pika, dotenv, asyncpg; \
import sqlalchemy, ahocorasick, alembic, httpx, websockets, yaml; \
print('All imports OK')"

COPY app/ ./app/
COPY static/ ./static/
COPY .env .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
