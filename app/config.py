from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import yaml


class ServerConfig(BaseModel):
    url: str
    api_key: Optional[str] = None
    max_concurrent_requests: int = 32


class ModelConfig(BaseModel):
    name: str
    servers: List[ServerConfig]


class HealthCheckConfig(BaseModel):
    interval_seconds: int = 60
    timeout_seconds: int = 5


class AppConfig(BaseModel):
    logging: bool = False
    health_check: HealthCheckConfig = HealthCheckConfig()
    models: List[ModelConfig]


def load_config(path: str = "config.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(config_path) as f:
        raw = yaml.safe_load(f)
    return AppConfig(**raw)
