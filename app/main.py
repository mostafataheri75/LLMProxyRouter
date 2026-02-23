from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import httpx
import asyncio

from app.config import load_config
from app.state import AppState
from app.services.health_checker import start_health_checker
from app.services.request_logger import RequestLogger
from app.routers import chat_completions, completions, models, embeddings, dashboard_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config("config.yaml")
    app.state.app_state = AppState(config)
    app.state.http_client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))
    app.state.request_logger = RequestLogger(enabled=config.logging)

    health_task = asyncio.create_task(
        start_health_checker(app.state.app_state, app.state.http_client)
    )
    app.state.health_task = health_task

    yield

    health_task.cancel()
    try:
        await health_task
    except asyncio.CancelledError:
        pass
    await app.state.http_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="LLM Proxy Router",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.include_router(chat_completions.router, prefix="/v1", tags=["OpenAI API"])
    app.include_router(completions.router, prefix="/v1", tags=["OpenAI API"])
    app.include_router(models.router, prefix="/v1", tags=["OpenAI API"])
    app.include_router(embeddings.router, prefix="/v1", tags=["OpenAI API"])
    app.include_router(dashboard_api.router, prefix="/api/dashboard", tags=["Dashboard"])

    templates = Jinja2Templates(directory="app/dashboard")

    @app.get("/dashboard", response_class=HTMLResponse, tags=["Dashboard"])
    async def dashboard(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    return app
