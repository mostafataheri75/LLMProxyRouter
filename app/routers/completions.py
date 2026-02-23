from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import CompletionRequest
from app.services.queue_manager import QueueManager
from app.services.proxy import forward_request

router = APIRouter()


@router.post("/completions")
async def completions(body: CompletionRequest, request: Request):
    state = request.app.state.app_state
    client = request.app.state.http_client
    req_logger = request.app.state.request_logger
    queue_mgr = QueueManager(state)

    model_name = body.model
    payload = body.model_dump(exclude_none=True)

    try:
        server = await queue_mgr.acquire_server(model_name)
    except ValueError:
        raise HTTPException(status_code=404, detail=f"Model not found: {model_name}")
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=429, detail=f"All servers busy for model: {model_name}")

    try:
        req_logger.log_request("POST", "/v1/completions", model_name, server.url, payload)
        response = await forward_request(client, server, "/v1/completions", payload)
        resp_data = response.json()
        req_logger.log_response(
            "/v1/completions", model_name, server.url,
            response.status_code, resp_data if response.status_code == 200 else None,
        )
        return JSONResponse(content=resp_data, status_code=response.status_code)
    except Exception as e:
        await state.record_metric(model_name, "request_error")
        raise HTTPException(status_code=502, detail=f"Backend error: {str(e)}")
    finally:
        await queue_mgr.release_server(model_name, server)
