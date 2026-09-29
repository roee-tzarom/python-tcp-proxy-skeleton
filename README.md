# JSON over TCP: Calculator and Caching Proxy

A small Python network service with three independently runnable pieces: a command-line client, a threaded calculator server and an optional caching proxy. Messages are newline-delimited JSON, so request and response boundaries remain visible when using a TCP byte stream.

## Request path

```text
client.py ── JSON line ──> proxy.py ── JSON line ──> server.py
                              │                        │
                       30-second response cache   AST calculator
                                                   + LRU cache
```

A client can connect directly to the server or through the proxy. The server parses calculator expressions with Python's `ast` module and evaluates only the supported numeric nodes, operators, functions and constants. It does not call Python `eval`. The server keeps an in-memory LRU result cache; the proxy has a separate, lock-protected response cache with a 30-second time to live.

## Run locally

The calculator path uses the Python 3 standard library. Start the server in one terminal:

```bash
python server.py --host 127.0.0.1 --port 5555
```

Then make a direct request in another:

```bash
python client.py --mode calc --expr "sqrt(16)+2*3"
```

To include the proxy, start it in a third terminal and point the client at port 5554:

```bash
python proxy.py --listen-port 5554 --server-port 5555
python client.py --host 127.0.0.1 --port 5554 --mode calc --expr "1+2*3"
```

`python client.py --interactive` opens a menu. The included smoke check uses pytest-style functions; with `pytest` installed, run `python -m pytest tests/test_smoke.py`.

## Wire format

A calculator request is one JSON object followed by a newline:

```json
{"mode":"calc","data":{"expr":"sqrt(16)+2*3"},"options":{"cache":true}}
```

Responses contain `ok`, either `result` or `error`, and timing/cache metadata for successful requests. The calculator supports arithmetic and selected functions such as `sqrt`, `sin` and `max`. Unsupported syntax produces an error response.

## Code map and behavior

| File | Responsibility |
| --- | --- |
| `server.py` | Restricted AST evaluation, JSON request dispatch, threaded connections and LRU storage |
| `proxy.py` | JSON-line forwarding, cache key normalization, TTL and lock protection |
| `client.py` | One-shot flags and interactive requests |
| `tests/test_smoke.py` | Focused calculator and cache checks |

The `gpt` request mode currently returns a stub message; it does not contact a model service. The server cache is process-local and is not synchronized between its worker threads. A client option that disables the server cache does not automatically bypass the proxy's separate cache. The protocol is intended for local inspection, not for exposing an internet-facing gateway.
