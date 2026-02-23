from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_bearer = HTTPBearer(auto_error=False)


async def verify_api_key(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> None:
    """
    Validates the client's Bearer token against proxy_api_keys.
    If proxy_api_keys is empty / not set, all requests are allowed through.
    """
    allowed_keys: list[str] | None = request.app.state.proxy_api_keys
    if not allowed_keys:
        return  # Auth disabled — open access

    if credentials is None or credentials.credentials not in allowed_keys:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
