from fastapi import APIRouter, Request

from app.models.schemas import ModelListResponse, ModelObject

router = APIRouter()


@router.get("/models")
async def list_models(request: Request):
    state = request.app.state.app_state
    models = []
    for model_name, model_state in state.models.items():
        has_healthy = any(s.healthy and not s.draining for s in model_state.servers)
        if has_healthy:
            models.append(ModelObject(id=model_name))
    return ModelListResponse(data=models)
