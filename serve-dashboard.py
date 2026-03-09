#!/usr/bin/env python3
"""
JARVIS Dashboard Server
Serves dashboard on http://localhost:8080 + refreshes data every 60s

Usage: python3 serve-dashboard.py
"""

import http.server
import threading
import time
import subprocess
import sys
import os
from pathlib import Path

PORT = 8080
ROOT = Path(__file__).parent
REFRESH_INTERVAL = 60  # seconds


def refresh_loop():
    while True:
        try:
            result = subprocess.run(
                [sys.executable, str(ROOT / "fetch_dashboard_data.py")],
                capture_output=True, text=True, cwd=ROOT
            )
            if result.returncode == 0:
                for line in result.stdout.strip().splitlines():
                    print(f"[data] {line}")
            else:
                print(f"[data] ⚠️  {result.stderr.strip()[:100]}")
        except Exception as e:
            print(f"[data] error: {e}")
        time.sleep(REFRESH_INTERVAL)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):
        pass  # suppress per-request logs


if __name__ == "__main__":
    os.chdir(ROOT)

    print(f"\n🚀 JARVIS Dashboard Server")
    print(f"   URL: http://localhost:{PORT}/dashboard.html")
    print(f"   Data refresh: every {REFRESH_INTERVAL}s")
    print(f"   Press Ctrl+C to stop\n")

    # Initial data fetch
    print("[data] Initial fetch...")
    subprocess.run([sys.executable, str(ROOT / "fetch_dashboard_data.py")], cwd=ROOT)

    # Background refresh thread
    t = threading.Thread(target=refresh_loop, daemon=True)
    t.start()

    # HTTP server
    with http.server.HTTPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n[server] Stopped.")
