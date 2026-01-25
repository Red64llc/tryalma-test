"""FastAPI application factory."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from tryalma import __version__
from tryalma.api.v1.router import router as v1_router
from tryalma.exceptions import APIError


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    application = FastAPI(
        title="TryAlma API",
        description="TryAlma REST API",
        version=__version__,
    )

    application.include_router(v1_router)

    @application.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    return application


app = create_app()
