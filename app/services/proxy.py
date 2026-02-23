import httpx
from typing import Any, Dict

from app.state import ServerState


async def forward_request(
    client: httpx.AsyncClient,
    server: ServerState,
    path: str,
    payload: Dict[str, Any],
) -> httpx.Response:
    base_url = server.url.rstrip("/")
    target_url = f"{base_url}{path}"

    payload_copy = dict(payload)
    payload_copy.pop("stream", None)
    payload_copy["stream"] = False

    headers = {}
    if server.api_key:
        headers["Authorization"] = f"Bearer {server.api_key}"

    response = await client.post(
        target_url,
        json=payload_copy,
        headers=headers,
        timeout=httpx.Timeout(120.0, connect=10.0),
    )
    return response
