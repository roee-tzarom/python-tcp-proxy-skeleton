# proxy.py
import argparse, socket, threading, json
import time

# Simple in-memory cache for proxy responses
CACHE_TTL_SECONDS = 30.0  # time-to-live for a cached response in seconds

_proxy_cache = {}
_proxy_cache_lock = threading.Lock()


def cache_get(key: str):
    """Return cached response bytes if still valid, otherwise None."""
    now = time.time()
    with _proxy_cache_lock:
        entry = _proxy_cache.get(key)
        if not entry:
            return None
        ts, resp_bytes = entry
        if now - ts > CACHE_TTL_SECONDS:
            # expired
            del _proxy_cache[key]
            return None
        return resp_bytes


def cache_set(key: str, resp_bytes: bytes):
    """Store response bytes in cache with current timestamp."""
    with _proxy_cache_lock:
        _proxy_cache[key] = (time.time(), resp_bytes)

def pipe(src, dst):
    """Bi-directional byte piping helper."""
    try:
        while True:
            data = src.recv(4096)
            if not data:
                break
            dst.sendall(data)
    except Exception:
        pass
    finally:
        try: dst.shutdown(socket.SHUT_WR)
        except Exception: pass

def main():
    ap = argparse.ArgumentParser(description="Transparent TCP proxy (optional)")
    ap.add_argument("--listen-host", default="127.0.0.1")
    ap.add_argument("--listen-port", type=int, default=5554)
    ap.add_argument("--server-host", default="127.0.0.1")
    ap.add_argument("--server-port", type=int, default=5555)
    args = ap.parse_args()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((args.listen_host, args.listen_port))
        s.listen(16)
        print(f"[proxy] {args.listen_host}:{args.listen_port} -> {args.server_host}:{args.server_port}")
        while True:
            c, addr = s.accept()
            threading.Thread(target=handle, args=(c, args.server_host, args.server_port), daemon=True).start()

def handle(c: socket.socket, sh: str, sp: int):
    """
    Handle a single client connection:
    - Read JSON lines from the client
    - Serve from proxy cache if possible
    - Otherwise forward to server and cache the response
    - Support multiple requests on the same TCP connection
    """
    with c:
        try:
            buffer = b""
            while True:
                chunk = c.recv(4096)
                if not chunk:
                    break
                buffer += chunk

                # process all complete lines in buffer
                while b"\n" in buffer:
                    line, _, buffer = buffer.partition(b"\n")
                    line = line.strip()
                    if not line:
                        continue

                    # parse client JSON request
                    try:
                        req_text = line.decode("utf-8")
                        req_obj = json.loads(req_text)
                    except Exception as e:
                        error = {
                            "ok": False,
                            "error": f"Proxy malformed request: {e}",
                        }
                        c.sendall((json.dumps(error) + "\n").encode("utf-8"))
                        continue

                    # normalize JSON to build a stable cache key
                    cache_key = json.dumps(req_obj, sort_keys=True)

                    # try proxy cache first
                    cached = cache_get(cache_key)
                    if cached is not None:
                        c.sendall(cached)
                        continue

                    # no cache: forward to real server
                    try:
                        with socket.create_connection((sh, sp), timeout=5) as s:
                            s.sendall(line + b"\n")

                            resp_buffer = b""
                            while True:
                                resp_chunk = s.recv(4096)
                                if not resp_chunk:
                                    break
                                resp_buffer += resp_chunk
                                if b"\n" in resp_buffer:
                                    resp_line, _, _ = resp_buffer.partition(b"\n")
                                    resp_bytes = resp_line + b"\n"

                                    # store in proxy cache
                                    cache_set(cache_key, resp_bytes)

                                    # send to client
                                    c.sendall(resp_bytes)
                                    break
                    except Exception as e:
                        error = {
                            "ok": False,
                            "error": f"Proxy error: {e}",
                        }
                        c.sendall((json.dumps(error) + "\n").encode("utf-8"))
        except Exception:
            # ignore unexpected exceptions on this client
            pass

if __name__ == "__main__":
    main()
