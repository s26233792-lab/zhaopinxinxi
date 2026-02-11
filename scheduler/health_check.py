"""
Health check API endpoint for monitoring.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
from json import dumps
import threading

from scheduler.monitor import health_check


class HealthCheckHandler(BaseHTTPRequestHandler):
    """HTTP handler for health check requests."""

    def do_GET(self):
        """Handle GET request."""
        if self.path == "/health":
            status = health_check()

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            response = dumps(status, ensure_ascii=False, indent=2)
            self.wfile.write(response.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def start_health_check_server(port: int = 8080):
    """
    Start health check HTTP server in background thread.

    Args:
        port: Port to listen on
    """
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)

    def run_server():
        server.serve_forever()

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()

    from loguru import logger
    logger.info(f"Health check server started on port {port}")
    logger.info(f"Visit http://localhost:{port}/health for status")
