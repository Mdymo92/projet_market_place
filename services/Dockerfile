# One image recipe for every Python service: docker compose passes SERVICE=auth|orders|...
# Build context is the repo root so the image can include the API contracts.
FROM python:3.12-slim

ARG SERVICE
ENV SERVICE_NAME=${SERVICE} \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/srv

WORKDIR /srv

COPY services/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY services/common/market_common /srv/market_common
COPY services/${SERVICE}/app /srv/app
COPY contracts /srv/contracts

RUN useradd --create-home --uid 10001 app
USER app

EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
