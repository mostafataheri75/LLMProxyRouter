"""
Integration test script for LLM Proxy Router.

Usage:
    python tests/integration_test.py [--base-url http://localhost:8080] [--output results.txt]

Discovers all online models via /v1/models, sends a test request to each,
prints results to CLI, and saves them to a file.
"""
import argparse
import httpx
import json
import sys
from datetime import datetime


EMBEDDING_KEYWORDS = ["embed", "bge", "e5", "gte"]


def is_embedding_model(model_name: str) -> bool:
    return any(kw in model_name.lower() for kw in EMBEDDING_KEYWORDS)


def main():
    parser = argparse.ArgumentParser(description="LLM Proxy Router Integration Test")
    parser.add_argument("--base-url", default="http://localhost:8080", help="Proxy base URL")
    parser.add_argument("--output", default="test_results.txt", help="Output file path")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    results = []
    client = httpx.Client(timeout=120.0)

    # Discover models
    print(f"[*] Querying models at {base}/v1/models ...")
    try:
        resp = client.get(f"{base}/v1/models")
    except httpx.ConnectError:
        print(f"[!] Could not connect to {base}. Is the proxy running?")
        sys.exit(1)

    if resp.status_code != 200:
        print(f"[!] Failed to fetch models: {resp.status_code}")
        sys.exit(1)

    models_data = resp.json()
    model_ids = [m["id"] for m in models_data.get("data", [])]
    print(f"[*] Found {len(model_ids)} online model(s): {model_ids}\n")

    if not model_ids:
        print("[!] No online models found. Check your config and backend servers.")
        sys.exit(0)

    # Test each model
    for model_id in model_ids:
        print(f"--- Testing: {model_id} ---")

        if is_embedding_model(model_id):
            endpoint = f"{base}/v1/embeddings"
            payload = {"model": model_id, "input": "Hello, world!"}
        else:
            endpoint = f"{base}/v1/chat/completions"
            payload = {
                "model": model_id,
                "messages": [{"role": "user", "content": "Say hello in one sentence."}],
                "max_tokens": 64,
            }

        try:
            resp = client.post(endpoint, json=payload)
            result = {
                "model": model_id,
                "endpoint": endpoint,
                "status_code": resp.status_code,
                "response": resp.json() if resp.status_code == 200 else resp.text,
            }
        except Exception as e:
            result = {
                "model": model_id,
                "endpoint": endpoint,
                "status_code": -1,
                "response": str(e),
            }

        results.append(result)
        print(json.dumps(result, indent=2, default=str))
        print()

    # Save results
    with open(args.output, "w") as f:
        f.write(f"LLM Proxy Router Integration Test Results\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Base URL: {base}\n")
        f.write(f"Models tested: {len(model_ids)}\n")
        f.write("=" * 60 + "\n\n")
        for r in results:
            f.write(json.dumps(r, indent=2, default=str))
            f.write("\n\n")

    print(f"[*] Results saved to {args.output}")

    passed = sum(1 for r in results if r["status_code"] == 200)
    failed = len(results) - passed
    print(f"\n[*] Summary: {passed} passed, {failed} failed out of {len(results)} model(s)")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
