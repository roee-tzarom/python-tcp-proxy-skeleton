# JSON over TCP: Calculator and Caching Proxy

A Python socket lab with a threaded server, a command-line client and a caching proxy. Requests and responses use newline-delimited JSON. The working calculator evaluates a restricted mathematical expression tree without `eval`.

## What is implemented

- `server.py`: `ast`-based calculator with selected operators, functions and constants; per-request cache option; in-memory LRU cache.
- `proxy.py`: JSON-line forwarding plus a separate lock-protected response cache with a 30-second TTL.
- `client.py`: one-shot requests and an interactive menu.
- `tests/test_smoke.py`: a small calculator/cache smoke test.

The `gpt` mode is a **stub** that returns a placeholder string. Installing the optional packages in `requirements.txt` or setting an API key does not turn it into a real AI integration.

## Run locally

Python 3 is required. The calculator and proxy use the standard library.

```bash
# Terminal 1
python server.py --host 127.0.0.1 --port 5555

# Terminal 2
python client.py --mode calc --expr "sqrt(16)+2*3"

# Optional terminal 3: proxy
python proxy.py --listen-port 5554 --server-port 5555
python client.py --host 127.0.0.1 --port 5554 --mode calc --expr "1+2*3"
```

Run `python client.py --interactive` for the menu. `--no-cache` disables the server cache for a one-shot request; the proxy has its own cache.

## Protocol example

```json
{"mode":"calc","data":{"expr":"sqrt(16)+2*3"},"options":{"cache":true}}
```

The response includes `ok`, `result` and cache/timing metadata. This is a local networking exercise, not a production gateway: caches are process-local, the server cache is not locked across request threads, and the proxy handles JSON-line traffic rather than arbitrary TCP streams.
