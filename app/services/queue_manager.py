import asyncio

from app.state import AppState, ServerState
from app.services.load_balancer import select_server


class QueueManager:
    def __init__(self, state: AppState):
        self.state = state

    async def acquire_server(self, model_name: str, timeout: float = 300.0) -> ServerState:
        model_state = self.state.get_model_state(model_name)
        if model_state is None:
            raise ValueError(f"Unknown model: {model_name}")

        any_healthy = any(
            s.healthy and not s.draining for s in model_state.servers
        )
        if not any_healthy:
            raise RuntimeError(f"No healthy servers available for model: {model_name}")

        # Fast path
        server = select_server(model_state)
        if server is not None:
            acquired = await server.acquire_slot()
            if acquired:
                await self.state.record_metric(model_name, "request_started")
                return server

        # Slow path: queue and wait
        await self.state.record_metric(model_name, "request_queued")
        loop = asyncio.get_event_loop()
        deadline = loop.time() + timeout

        while True:
            remaining = deadline - loop.time()
            if remaining <= 0:
                raise TimeoutError(f"Queue timeout for model: {model_name}")

            model_state.slot_available.clear()

            server = select_server(model_state)
            if server is not None:
                acquired = await server.acquire_slot()
                if acquired:
                    await self.state.record_metric(model_name, "request_started")
                    return server

            try:
                await asyncio.wait_for(
                    model_state.slot_available.wait(),
                    timeout=min(remaining, 5.0),
                )
            except asyncio.TimeoutError:
                continue

    async def release_server(self, model_name: str, server: ServerState) -> None:
        await server.release_slot()
        await self.state.record_metric(model_name, "request_completed")

        model_state = self.state.get_model_state(model_name)
        if model_state:
            model_state.slot_available.set()
