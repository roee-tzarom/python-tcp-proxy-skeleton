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


## Request path and safety choices

The client sends one JSON object per line to a TCP endpoint. `server.py` handles connections with threads, decodes the request and dispatches by mode. For calculator requests, it parses an expression with Python's `ast` module and evaluates only a permitted subset of nodes, operators, functions and constants. It does not pass untrusted input to Python `eval`. The server's in-memory LRU cache can reuse calculator results. The proxy forwards the same JSON-line protocol and optionally serves a result from its own lock-protected cache until the 30-second TTL expires.

```text
client.py  →  proxy.py (optional TTL cache)  →  server.py (AST calculator)
                JSON line over TCP                JSON response
```

The two caches are distinct: disabling the server cache with a client option does not automatically bypass a separately running proxy cache. `tests/test_smoke.py` checks a small calculator/cache path, and the interactive client is useful for manual requests.

## Repository map and limitations

| File | What to inspect |
| --- | --- |
| `server.py` | AST whitelist, request dispatch and LRU storage |
| `proxy.py` | Request forwarding, cache keying, TTL and locking |
| `client.py` | One-shot flags and interactive menu |
| `tests/test_smoke.py` | Runnable behavior checks |

The `gpt` branch is a placeholder response, even though the repository has optional dependency names. There is no live model call. The server cache is not synchronized across worker threads, and the wire format is a line-oriented lab protocol rather than an arbitrary-stream or hardened internet-facing proxy.
