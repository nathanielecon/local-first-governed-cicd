import logging
import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field
from starlette.middleware.base import RequestResponseEndpoint

from delivery_api.config import Settings, get_settings
from delivery_api.logging import configure_logging

logger = logging.getLogger("delivery_api.requests")


class QuoteRequest(BaseModel):
    units: int = Field(ge=1, le=1000)
    unit_price: float = Field(gt=0, le=1_000_000)
    discount_percent: float = Field(default=0, ge=0, le=100)


class QuoteResponse(BaseModel):
    subtotal: float
    discount: float
    total: float
    currency: str = "USD"


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        logging.getLogger("delivery_api.lifecycle").info(
            "service_started", extra={"request_id": "system"}
        )
        yield
        logging.getLogger("delivery_api.lifecycle").info(
            "service_stopped", extra={"request_id": "system"}
        )

    app = FastAPI(title=app_settings.name, version=app_settings.version, lifespan=lifespan)

    @app.middleware("http")
    async def request_context(request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )
            raise
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["x-request-id"] = request_id
        logger.info(
            "request_completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        return response

    @app.get("/health/live")
    async def live() -> dict[str, str]:
        return {"status": "live"}

    @app.get("/health/ready")
    async def ready() -> dict[str, str]:
        if not app_settings.ready:
            raise HTTPException(status_code=503, detail="service is not ready")
        return {"status": "ready"}

    @app.get("/version")
    async def version() -> dict[str, str]:
        return {
            "name": app_settings.name,
            "version": app_settings.version,
            "git_sha": app_settings.git_sha,
            "environment": app_settings.environment,
        }

    @app.post("/quotes", response_model=QuoteResponse)
    async def quote(request: QuoteRequest) -> QuoteResponse:
        subtotal = round(request.units * request.unit_price, 2)
        discount = round(subtotal * request.discount_percent / 100, 2)
        return QuoteResponse(
            subtotal=subtotal,
            discount=discount,
            total=round(subtotal - discount, 2),
        )

    return app


app = create_app()
