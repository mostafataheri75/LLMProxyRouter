import asyncio
import httpx
from datetime import datetime

from app.state import AppState, ServerState


async def check_server_health(server_state: 'ServerState', client: httpx.AsyncClient, timeout: int) -> bool:
    try:
        headers = {}
        if server_state.api_key:
            headers["Authorization"] = f"Bearer {server_state.api_key}"
        url = server_state.url.rstrip("/")
        response = await client.get(f"{url}/health", headers=headers, timeout=timeout)
        return response.status_code == 200
    except (httpx.RequestError, httpx.TimeoutException):
        return False


async def run_health_checks(state: AppState, client: httpx.AsyncClient) -> None:
    timeout = state.config.health_check.timeout_seconds
    tasks = {}
    for url, server_state in state.servers.items():
        tasks[url] = asyncio.create_task(check_server_health(server_state, client, timeout))

    for url, task in tasks.items():
        is_healthy = await task
        server_state = state.servers[url]
        server_state.healthy = is_healthy
        server_state.last_health_check = datetime.utcnow()


async def start_health_checker(state: AppState, client: httpx.AsyncClient) -> None:
    await run_health_checks(state, client)
    while True:
        await asyncio.sleep(state.config.health_check.interval_seconds)
        await run_health_checks(state, client)
