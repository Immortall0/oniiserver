"""
SimpleChat - HTTP Chat Client
Usage: python client.py [server_ip] [port]
  server_ip  : IP address of the server (default: 127.0.0.1)
  port       : Server port (default: 8888)

Example:
  python client.py                      # connect to localhost
  python client.py 192.168.1.10         # connect to someone on LAN
  python client.py 192.168.1.10 9000    # custom port
"""

import sys
import json
import time
import threading
import urllib.request
import urllib.error
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
SERVER_IP   = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
SERVER_PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8888
BASE_URL    = f"http://{SERVER_IP}:{SERVER_PORT}"
POLL_INTERVAL = 1.0   # seconds between GET polls

# ── State ─────────────────────────────────────────────────────────────────────
last_timestamp = 0.0
username = ""
running = True

# ── Helpers ───────────────────────────────────────────────────────────────────

def http_get(path, timeout=5):
    url = BASE_URL + path
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def http_post(path, data, timeout=5):
    url = BASE_URL + path
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def clear_line():
    """Erase the current input line so incoming messages print cleanly."""
    sys.stdout.write("\r\033[K")
    sys.stdout.flush()


def print_message(msg):
    """Print a received message above the input prompt."""
    clear_line()
    ts = msg.get("time_str", "")
    name = msg.get("name", "?")
    text = msg.get("text", "")
    # Highlight own messages differently
    if name == username:
        print(f"  \033[96m[{ts}] {name} (you)\033[0m: {text}")
    else:
        print(f"  \033[93m[{ts}] {name}\033[0m: {text}")
    # Re-draw the prompt
    sys.stdout.write(f"\033[90m> \033[0m")
    sys.stdout.flush()

# ── Background poller ─────────────────────────────────────────────────────────

def poll_loop():
    global last_timestamp, running
    while running:
        try:
            msgs = http_get(f"/messages?since={last_timestamp}")
            for msg in msgs:
                # Don't echo back our own just-sent messages
                # (server echoes them; we skip those we already printed locally)
                print_message(msg)
                if msg["timestamp"] > last_timestamp:
                    last_timestamp = msg["timestamp"]
        except urllib.error.URLError:
            pass  # Server unreachable — just keep retrying
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    global username, running, last_timestamp

    print("\n" + "=" * 50)
    print("  SimpleChat CLIENT")
    print("=" * 50)
    print(f"  Server : {BASE_URL}")

    # ── Ask for username ───────────────────────────────────────────────────────
    while True:
        name = input("  Your name: ").strip()
        if name:
            username = name
            break
        print("  Name cannot be empty.")

    # ── Test connection ────────────────────────────────────────────────────────
    print(f"\n  Connecting to {BASE_URL} ...")
    try:
        msgs = http_get("/messages")
        # Seed last_timestamp so we only see NEW messages from now on
        if msgs:
            last_timestamp = max(m["timestamp"] for m in msgs)
        print(f"  Connected! ({len(msgs)} existing message(s) in chat)")
    except urllib.error.URLError as e:
        print(f"  ERROR: Cannot reach server — {e.reason}")
        print("  Make sure server.py is running and the IP/port are correct.")
        sys.exit(1)

    print(f"\n  Welcome, \033[96m{username}\033[0m! Type a message and press Enter.")
    print("  Type  /quit  or press Ctrl+C to exit.")
    print("-" * 50 + "\n")

    # ── Start background poller ────────────────────────────────────────────────
    t = threading.Thread(target=poll_loop, daemon=True)
    t.start()

    # ── Input loop ─────────────────────────────────────────────────────────────
    try:
        while True:
            sys.stdout.write("\033[90m> \033[0m")
            sys.stdout.flush()
            text = input().strip()

            if not text:
                continue

            if text.lower() in ("/quit", "/exit", "/q"):
                break

            # Send message
            try:
                http_post("/send", {"name": username, "text": text})
            except urllib.error.URLError:
                clear_line()
                print("  \033[91m[Error] Could not send — server unreachable.\033[0m")

    except (KeyboardInterrupt, EOFError):
        pass

    running = False
    print("\n\n  Disconnected. Bye!\n")


if __name__ == "__main__":
    main()
