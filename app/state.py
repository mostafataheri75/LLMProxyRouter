import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from app.config import AppConfig


@dataclass
class MetricsRecord:
    timestamp: datetime
    model_name: str
    event: str  # "request_started", "request_completed", "request_error", "request_queued"


@dataclass
class ServerState:
    url: str
    max_concurrent_requests: int
    api_key: Optional[str] = None
    current_requests: int = 0
    healthy: bool = False
    draining: bool = False
    last_health_check: Optional[datetime] = None
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def acquire_slot(self) -> bool:
        async with self._lock:
            if self.current_requests < self.max_concurrent_requests:
                self.current_requests += 1
                return True
            return False

    async def release_slot(self) -> None:
        async with self._lock:
            self.current_requests = max(0, self.current_requests - 1)


@dataclass
class ModelState:
    name: str
    servers: List[ServerState]
    slot_available: asyncio.Event = field(default_factory=asyncio.Event)


class AppState:
    def __init__(self, config: AppConfig):
        self.config = config
        self.models: Dict[str, ModelState] = {}
        self.servers: Dict[str, ServerState] = {}
        self.metrics_log: List[MetricsRecord] = []
        self._metrics_lock = asyncio.Lock()

        for model_cfg in config.models:
            server_states = []
            for srv_cfg in model_cfg.servers:
                if srv_cfg.url not in self.servers:
                    self.servers[srv_cfg.url] = ServerState(
                        url=srv_cfg.url,
                        max_concurrent_requests=srv_cfg.max_concurrent_requests,
                        api_key=srv_cfg.api_key,
                    )
                server_states.append(self.servers[srv_cfg.url])
            self.models[model_cfg.name] = ModelState(
                name=model_cfg.name,
                servers=server_states,
            )

    def get_model_state(self, model_name: str) -> Optional[ModelState]:
        return self.models.get(model_name)

    async def record_metric(self, model_name: str, event: str) -> None:
        async with self._metrics_lock:
            self.metrics_log.append(MetricsRecord(
                timestamp=datetime.utcnow(),
                model_name=model_name,
                event=event,
            ))
            cutoff = datetime.utcnow() - timedelta(minutes=60)
            self.metrics_log = [
                m for m in self.metrics_log if m.timestamp >= cutoff
            ]
