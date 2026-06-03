"""
SimpleChat - HTTP Chat Server
Run this first, then run client.py on any machine in the same network.
Usage: python server.py [port]  (default port: 8888)
"""

import sys
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# In-memory message store
messages = []

class ChatHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Client polls this to fetch new messages."""
        if self.path.startswith("/messages"):
            # Optional ?since=<timestamp> param to only get new messages
            since = 0.0
            if "?since=" in self.path:
                try:
                    since = float(self.path.split("?since=")[1])
                except ValueError:
                    pass

            new_msgs = [m for m in messages if m["timestamp"] > since]
            self._send_json(200, new_msgs)
        else:
            self._send_json(404, {"error": "Not found"})

    def do_POST(self):
        """Client sends a message here."""
        if self.path == "/send":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                name = data.get("name", "Anonymous").strip() or "Anonymous"
                text = data.get("text", "").strip()

                if not text:
                    self._send_json(400, {"error": "Empty message"})
                    return

                msg = {
                    "id": len(messages) + 1,
                    "name": name,
                    "text": text,
                    "timestamp": time.time(),
                    "time_str": datetime.now().strftime("%H:%M:%S"),
                }
                messages.append(msg)

                # Also print to server console
                print(f"  [{msg['time_str']}] {name}: {text}")
                self._send_json(200, {"status": "ok", "id": msg["id"]})
            except json.JSONDecodeError:
                self._send_json(400, {"error": "Invalid JSON"})
        else:
            self._send_json(404, {"error": "Not found"})

    def _send_json(self, code, data):
        body = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Suppress default HTTP logs for cleaner output


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8888
    server = HTTPServer(("0.0.0.0", port), ChatHandler)

    print("=" * 50)
    print("  SimpleChat SERVER")
    print("=" * 50)
    print(f"  Listening on port {port}")
    print(f"  Share your IP so others can connect.")
    print(f"  Messages will appear here as they arrive.")
    print("  Press Ctrl+C to stop.")
    print("=" * 50)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")


if __name__ == "__main__":
    main()
