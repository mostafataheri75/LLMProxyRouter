import logging
import json
from typing import Any, Dict, Optional

logger = logging.getLogger("llm_proxy.requests")


class RequestLogger:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        if enabled:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter(
                "%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
            ))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

    def log_request(
        self,
        method: str,
        path: str,
        model: str,
        server_url: str,
        payload: Dict[str, Any],
    ) -> None:
        if not self.enabled:
            return
        logger.info(
            "REQUEST | %s %s | model=%s | server=%s | payload=%s",
            method, path, model, server_url,
            json.dumps(payload, default=str)[:500],
        )

    def log_response(
        self,
        path: str,
        model: str,
        server_url: str,
        status_code: int,
        response_body: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> None:
        if not self.enabled:
            return
        body_preview = json.dumps(response_body, default=str)[:500] if response_body else "N/A"
        logger.info(
            "RESPONSE | %s | model=%s | server=%s | status=%d | error=%s | body=%s",
            path, model, server_url, status_code, error or "none", body_preview,
        )
