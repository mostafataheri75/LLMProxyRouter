from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()


class ServerStatusItem(BaseModel):
    url: str
    healthy: bool
    draining: bool
    current_requests: int
    max_concurrent_requests: int
    last_health_check: Optional[str]


class ModelMetricsItem(BaseModel):
    model_name: str
    total_in_flight: int
    processing: int
    queued: int


class ToggleRequest(BaseModel):
    url: str
    draining: bool


@router.get("/status")
async def server_status(request: Request) -> List[ServerStatusItem]:
    state = request.app.state.app_state
    result = []
    for url, srv in state.servers.items():
        result.append(ServerStatusItem(
            url=srv.url,
            healthy=srv.healthy,
            draining=srv.draining,
            current_requests=srv.current_requests,
            max_concurrent_requests=srv.max_concurrent_requests,
            last_health_check=srv.last_health_check.isoformat() if srv.last_health_check else "never",
        ))
    return result


@router.get("/metrics")
async def model_metrics(request: Request) -> List[ModelMetricsItem]:
    state = request.app.state.app_state
    cutoff = datetime.utcnow() - timedelta(minutes=60)
    result = []

    for model_name, model_state in state.models.items():
        in_flight = sum(s.current_requests for s in model_state.servers)

        queued_count = 0
        started_count = 0
        for record in state.metrics_log:
            if record.model_name == model_name and record.timestamp >= cutoff:
                if record.event == "request_queued":
                    queued_count += 1
                elif record.event == "request_started":
                    started_count += 1

        current_queued = max(0, queued_count - started_count)

        result.append(ModelMetricsItem(
            model_name=model_name,
            total_in_flight=in_flight + current_queued,
            processing=in_flight,
            queued=current_queued,
        ))
    return result


@router.post("/toggle")
async def toggle_drain(body: ToggleRequest, request: Request):
    state = request.app.state.app_state
    srv = state.servers.get(body.url)
    if srv is None:
        raise HTTPException(status_code=404, detail=f"Server not found: {body.url}")
    srv.draining = body.draining
    return {"status": "ok", "url": body.url, "draining": srv.draining}
