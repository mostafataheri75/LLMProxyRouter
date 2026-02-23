# LLM Proxy Router

An OpenAI-compatible API proxy router that manages, queues, and load-balances requests across multiple local vLLM servers.

## Features

- **OpenAI API Compatibility** — Supports `/v1/chat/completions`, `/v1/completions`, `/v1/models`, and `/v1/embeddings`
- **Dynamic Health Checking** — Polls all backend servers every 60 seconds; only routes to healthy servers
- **Least-Connections Load Balancing** — Distributes requests evenly across available backends
- **Concurrency Limits & Queuing** — Per-server concurrency caps with automatic request queuing when all servers are busy
- **Web Dashboard** — Real-time monitoring with server status, model metrics, and drain toggles
- **Optional Request Logging** — Configurable via YAML toggle

## Quick Start

### 1. Create a virtual environment and install dependencies

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
# venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 2. Configure

Edit `config.yaml` to point at your vLLM servers. See `sample_files/config_sample.yaml` for a commented example.

```yaml
logging: false

health_check:
  interval_seconds: 60
  timeout_seconds: 5

models:
  - name: "meta-llama/Llama-3.1-8B-Instruct"
    servers:
      - url: "http://gpu-server-1:8000"
        max_concurrent_requests: 32
      - url: "http://gpu-server-2:8000"
        max_concurrent_requests: 32
```

### 3. Run

```bash
python run.py
```

The router starts on `http://0.0.0.0:8080`.

### 4. Use

Send requests exactly as you would to the OpenAI API:

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 64
  }'
```

List available models:

```bash
curl http://localhost:8080/v1/models
```

### 5. Dashboard

Open `http://localhost:8080/dashboard` in a browser. The dashboard auto-refreshes every 10 seconds and shows:

- **Server Status** — Health, in-flight requests, and ON/OFF drain toggle per server
- **Model Metrics** — Total in-flight, processing, and queued requests per model (last 60 minutes)

## Configuration Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `logging` | bool | `false` | Enable request/response logging to stdout |
| `health_check.interval_seconds` | int | `60` | Seconds between health check rounds |
| `health_check.timeout_seconds` | int | `5` | Timeout per health check request |
| `models[].name` | string | required | Model identifier (must match vLLM's model name) |
| `models[].servers[].url` | string | required | Backend vLLM server URL |
| `models[].servers[].max_concurrent_requests` | int | `32` | Max in-flight requests for this server |

## Integration Test

Run the integration test to verify all online models are reachable:

```bash
python tests/integration_test.py --base-url http://localhost:8080 --output test_results.txt
```

The script discovers models via `/v1/models`, sends a test request to each, prints results, and saves them to the output file.

## Project Structure

```
LLM-farm/
├── run.py                     # Entry point
├── config.yaml                # Your configuration
├── requirements.txt           # Python dependencies
├── sample_files/
│   └── config_sample.yaml     # Annotated example config
├── app/
│   ├── main.py                # FastAPI app factory
│   ├── config.py              # Config loader
│   ├── state.py               # Runtime state management
│   ├── models/
│   │   └── schemas.py         # OpenAI request/response schemas
│   ├── routers/
│   │   ├── chat_completions.py
│   │   ├── completions.py
│   │   ├── models.py
│   │   ├── embeddings.py
│   │   └── dashboard_api.py
│   ├── services/
│   │   ├── health_checker.py  # Background health polling
│   │   ├── load_balancer.py   # Least-connections selection
│   │   ├── proxy.py           # HTTP forwarding to backends
│   │   ├── queue_manager.py   # Concurrency & queuing
│   │   └── request_logger.py  # Optional logging
│   └── dashboard/
│       └── index.html         # Web dashboard
└── tests/
    └── integration_test.py    # Integration test script
```
