FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN pip install --no-cache-dir poetry \
    && poetry config virtualenvs.create false \
    && poetry install --only main --no-root --no-interaction \
    && playwright install --with-deps chromium \
    && rm -rf /root/.cache/pip

COPY rpa_api/ ./rpa_api/

EXPOSE 8000

CMD ["fastapi", "run", "rpa_api/app.py", "--host", "0.0.0.0", "--port", "8000"]
