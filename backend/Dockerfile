FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.1.2" && \
    pip install --no-cache-dir .
COPY . .
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
