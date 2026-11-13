"""Builds a FastAPI app with what every service needs: /health, /metrics, JSON logs, traces."""

import logging

from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from .config import get_settings
from .logging import setup_logging

log = logging.getLogger(__name__)


def _setup_tracing(app: FastAPI, service: str, endpoint: str) -> None:
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:  # tracing is optional for local unit tests
        log.info("opentelemetry not installed, tracing disabled")
        return

    provider = TracerProvider(resource=Resource.create({"service.name": service}))
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True)))
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,metrics")
    HTTPXClientInstrumentor().instrument()  # propagates the trace to inventory / payment


def create_app(service: str, title: str, version: str = "1.0.0") -> FastAPI:
    settings = get_settings()
    setup_logging(service, settings.log_format)

    app = FastAPI(title=title, version=version)

    @app.get("/health", include_in_schema=False)
    def health() -> dict:
        return {"status": "ok", "service": service}

    Instrumentator(excluded_handlers=["/health", "/metrics"]).instrument(app).expose(app, include_in_schema=False)

    if settings.otel_exporter_otlp_endpoint:
        _setup_tracing(app, service, settings.otel_exporter_otlp_endpoint)

    return app
