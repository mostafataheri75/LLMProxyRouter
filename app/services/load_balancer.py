from typing import Optional, List

from app.state import ServerState, ModelState


def select_server(model_state: ModelState) -> Optional[ServerState]:
    candidates: List[ServerState] = [
        s for s in model_state.servers
        if s.healthy and not s.draining and s.current_requests < s.max_concurrent_requests
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda s: s.current_requests)
