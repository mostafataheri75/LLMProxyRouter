import argparse
import uvicorn
from app.main import create_app


def parse_args():
    parser = argparse.ArgumentParser(description="LLM Proxy Router")
    parser.add_argument(
        "--proxy-api-key",
        action="append",
        dest="proxy_api_keys",
        default=None,
        help="API key required for clients to access the proxy. "
             "Can be specified multiple times. Merged with proxy_api_keys in config.yaml.",
    )
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8080, help="Bind port (default: 8080)")
    return parser.parse_args()


args = parse_args()
app = create_app(proxy_api_keys=args.proxy_api_keys)

if __name__ == "__main__":
    uvicorn.run("run:app", host=args.host, port=args.port, reload=False)
