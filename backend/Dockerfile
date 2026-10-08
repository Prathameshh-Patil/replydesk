# The image that runs the API: Python 3.12 plus our libraries plus our code and agent files.
# Built from the repo root (see docker-compose.yml) so it can include the agents/ folder.
FROM python:3.12-slim

# Don't write .pyc files; print logs immediately instead of buffering them.
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 AGENTS_DIR=/app/agents

WORKDIR /app

# Install libraries first, so Docker can reuse this layer when only the code changes.
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/alembic.ini .
COPY backend/alembic ./alembic
COPY backend/app ./app
COPY agents ./agents

EXPOSE 8000
# Bring the database up to the latest migration, then start the API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
