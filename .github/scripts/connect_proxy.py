"""Minimal logging HTTP CONNECT proxy, used by CI only.

Usage: python connect_proxy.py PORT LOGFILE

If PROXY_USER and PROXY_PASSWORD are set, clients must log in with them.

Each tunnel is logged as "CONNECT host:port", so CI can prove that a tool
really went through the proxy instead of connecting directly.
"""

import base64
import os
import select
import socket
import socketserver
import sys
import threading

PORT = int(sys.argv[1])
LOGFILE = sys.argv[2]
LOG_LOCK = threading.Lock()
EXPECTED_AUTH = None
if os.environ.get("PROXY_USER"):
    credentials = f"{os.environ['PROXY_USER']}:{os.environ['PROXY_PASSWORD']}"
    EXPECTED_AUTH = "Basic " + base64.b64encode(credentials.encode()).decode()


def log(line):
    with LOG_LOCK, open(LOGFILE, "a", encoding="ascii", errors="replace") as f:
        f.write(line + "\n")


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        head = b""
        while b"\r\n\r\n" not in head:
            chunk = self.request.recv(4096)
            if not chunk:
                return
            head += chunk

        lines = head.split(b"\r\n\r\n", 1)[0].decode("latin-1").split("\r\n")
        method, target = lines[0].split(" ")[:2]
        headers = dict((k.strip().lower(), v.strip()) for k, _, v in (h.partition(":") for h in lines[1:]))

        if EXPECTED_AUTH and headers.get("proxy-authorization") != EXPECTED_AUTH:
            reason = "wrong login" if "proxy-authorization" in headers else "no login"
            log(f"DENIED {target} ({reason})")
            self.request.sendall(
                b"HTTP/1.1 407 Proxy Authentication Required\r\n"
                b'Proxy-Authenticate: Basic realm="ci"\r\n'
                b"Content-Length: 0\r\nConnection: close\r\n\r\n"
            )
            return

        log(f"{method} {target}")
        if method != "CONNECT":
            self.request.sendall(b"HTTP/1.1 405 Method Not Allowed\r\n\r\n")
            return

        host, port = target.rsplit(":", 1)
        try:
            upstream = socket.create_connection((host, int(port)), timeout=20)
        except OSError:
            self.request.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            return

        with upstream:
            self.request.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            # Forward anything the client sent straight after its headers
            early = head.split(b"\r\n\r\n", 1)[1]
            if early:
                upstream.sendall(early)
            peers = {self.request: upstream, upstream: self.request}
            while True:
                readable, _, _ = select.select(list(peers), [], [], 60)
                if not readable:
                    return
                for sock in readable:
                    try:
                        data = sock.recv(65536)
                        if not data:
                            return
                        peers[sock].sendall(data)
                    except OSError:
                        return


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


with Server(("127.0.0.1", PORT), Handler) as server:
    log("LISTENING")
    server.serve_forever()
