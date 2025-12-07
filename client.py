# client.py
import argparse, socket, json, sys

def request(host: str, port: int, payload: dict) -> dict:
    """Send a single JSON-line request and return a single JSON-line response."""
    data = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
    with socket.create_connection((host, port), timeout=5) as s:
        s.sendall(data)
        buff = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buff += chunk
            if b"\n" in buff:
                line, _, _ = buff.partition(b"\n")
                return json.loads(line.decode("utf-8"))
    return {"ok": False, "error": "No response"}

# Example expressions for calc mode (added by student)
DEFAULT_CALC_EXPRS = [
    "1+2*3",
    "sin(2+3*4)",
    "sqrt(16)",
    "cos(pi/3)**2 + sin(pi/3)**2",
]

def interactive_client(host: str, port: int):
    """
    Interactive client mode:
    - lets the user choose calc or gpt
    - choose from predefined expressions or type a custom one
    - send multiple requests until the user chooses to exit
    """
    print(f"Interactive mode. Server: {host}:{port}")

    while True:
        print("\nChoose mode:")
        print("1) calc - evaluate math expression")
        print("2) gpt  - send prompt to GPT (stub)")
        print("3) exit")
        choice = input("Your choice: ").strip()

        if choice == "3":
            print("Exiting interactive mode.")
            break

        if choice == "1":
            # calc mode: choose predefined or custom expression
            print("\nCalc mode:")
            print("Predefined expressions:")
            for i, expr in enumerate(DEFAULT_CALC_EXPRS, start=1):
                print(f"{i}) {expr}")
            print(f"{len(DEFAULT_CALC_EXPRS)+1}) custom expression")

            sel = input("Select number: ").strip()
            try:
                idx = int(sel)
            except ValueError:
                idx = len(DEFAULT_CALC_EXPRS) + 1

            if 1 <= idx <= len(DEFAULT_CALC_EXPRS):
                expr = DEFAULT_CALC_EXPRS[idx - 1]
            else:
                expr = input("Enter expression: ")

            payload = {
                "mode": "calc",
                "data": {"expr": expr},
                "options": {"cache": True},
            }

        elif choice == "2":
            # gpt mode
            print("\nGPT mode:")
            prompt = input("Enter prompt: ")
            payload = {
                "mode": "gpt",
                "data": {"prompt": prompt},
                "options": {"cache": True},
            }

        else:
            print("Invalid choice, please try again.")
            continue

        # Send request to server
        resp = request(host, port, payload)
        print("\n--- Server response ---")
        print(json.dumps(resp, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Client (calc/gpt over JSON TCP)")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5555)
    ap.add_argument("--mode", choices=["calc", "gpt"], help="Single request mode")
    ap.add_argument("--expr", help="Expression for mode=calc")
    ap.add_argument("--prompt", help="Prompt for mode=gpt")
    ap.add_argument("--no-cache", action="store_true", help="Disable caching")
    ap.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive menu mode",
    )
    args = ap.parse_args()

    if args.interactive:
        interactive_client(args.host, args.port)
        return

    if not args.mode:
        print("Missing --mode (or use --interactive)", file=sys.stderr)
        sys.exit(2)

    if args.mode == "calc":
        if not args.expr:
            print("Missing --expr", file=sys.stderr)
            sys.exit(2)
        payload = {
            "mode": "calc",
            "data": {"expr": args.expr},
            "options": {"cache": not args.no_cache},
        }
    else:  # mode == "gpt"
        if not args.prompt:
            print("Missing --prompt", file=sys.stderr)
            sys.exit(2)
        payload = {
            "mode": "gpt",
            "data": {"prompt": args.prompt},
            "options": {"cache": not args.no_cache},
        }

    resp = request(args.host, args.port, payload)
    print(json.dumps(resp, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
