"""Local static and API server using the Lambda handler."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import mimetypes
import os
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .handler import handler as lambda_handler


class RequestHandler(BaseHTTPRequestHandler):
    static_dir = Path(os.getenv("STATIC_DIR", "build/site")).resolve()

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/") or parsed.path == "/health":
            query = {
                key: values[-1]
                for key, values in parse_qs(parsed.query, keep_blank_values=True).items()
            }
            response = lambda_handler(
                {"rawPath": parsed.path, "queryStringParameters": query},
                None,
            )
            body = response["body"].encode("utf-8")
            self.send_response(response["statusCode"])
            for name, value in response.get("headers", {}).items():
                self.send_header(name, value)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        requested = parsed.path.lstrip("/") or "index.html"
        target = (self.static_dir / requested).resolve()
        if self.static_dir not in target.parents and target != self.static_dir:
            self.send_error(404)
            return
        if not target.is_file():
            target = self.static_dir / "index.html"
        if not target.is_file():
            self.send_error(404)
            return

        body = target.read_bytes()
        content_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), RequestHandler)
    print(f"ELA Seasonality Dashboard: http://{args.host}:{args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
