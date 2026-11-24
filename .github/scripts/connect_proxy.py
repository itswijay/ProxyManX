"""Minimal logging HTTP CONNECT proxy, used by CI only.

Usage: python connect_proxy.py PORT LOGFILE

Each tunnel is logged as "CONNECT host:port", so CI can prove that a tool
really went through the proxy instead of connecting directly.
"""

import select
import socket
import socketserver
import sys
import threading

PORT = int(sys.argv[1])
LOGFILE = sys.argv[2]
LOG_LOCK = threading.Lock()


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

        method, target = head.split(b"\r\n", 1)[0].decode("latin-1").split(" ")[:2]
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
