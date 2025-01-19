import logging
import signal
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler
from typing import Callable, Optional

from funnel.exceptions import BadRequestError, FunnelError
from funnel.request import Request
from funnel.router import Router
from funnel.utils import load_config, mount_directories

BUFFER_SIZE = 1024

rotating_file_handler = RotatingFileHandler(
    "logs/server.log", maxBytes=5 * 1024 * 1024
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[rotating_file_handler, logging.StreamHandler()],
)

logger = logging.getLogger("HTTP Server")


class HTTPServer:
    """
    A basic HTTP server supporting configuration,
    routing, and request handling.
    """

    def __init__(self, config_path: str):
        config = load_config(config_path)

        self.host = config.get("host", "127.0.0.1")
        self.port = config.get("port", 8080)

        self.router = Router()
        self.executor = ThreadPoolExecutor(
            max_workers=config.get("max_workers", 10)
        )
        self._running = threading.Event()
        self._running.set()

        self._server_socket: socket.socket | None = None

        mount_directories(self.router, config)

        self._mounted_directories = config.get("mounted_directories", [])

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, sig, _) -> None:
        """
        Handle a signal to stop the server.
        """
        signal_name = signal.Signals(sig).name
        logger.info(f"Received signal {signal_name}. Stopping server...")
        self.stop()

    def start(self) -> None:
        """
        Start the HTTP server and listen for incoming requests.
        """
        logger.info(f"Starting server on {self.host}:{self.port}...")
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
        )
        self._server_socket.bind((self.host, self.port))
        self._server_socket.listen(256)
        self._server_socket.settimeout(1)

        logger.info(f"Server is running on http://{self.host}:{self.port}")

        try:
            while self._running.is_set():
                try:
                    client_socket, client_address = (
                        self._server_socket.accept()
                    )
                    logger.info(f"Accepted connection from {client_address}")
                    self.executor.submit(self._handle_request, client_socket)
                except socket.timeout:
                    continue
                except OSError as e:
                    if not self._running.is_set():
                        logger.info("Server socket has been closed.")
                        break
                    logger.error(f"Socket error: {e}", exc_info=True)
        except Exception as e:
            logger.critical(f"An error occurred: {e}", exc_info=True)
        finally:
            self.stop()

    def stop(self) -> None:
        """
        Stop the server gracefully.
        """
        if not self._running.is_set():
            return
        self._running.clear()

        if self._server_socket:
            try:
                self._server_socket.close()
                logger.info("Server socket closed.")
            except OSError:
                pass

        self.executor.shutdown(wait=True)
        logger.info("All threads have been stopped.")

    def _handle_request(self, client_socket: socket.socket) -> None:
        """
        Handle an incoming HTTP request with Content-Length validation.

        Args:
            client_socket (socket.socket): The client's socket connection.
        """
        try:
            start_time = time.perf_counter()
            client_socket.settimeout(5)
            raw_request = self._receive_headers(client_socket)

            headers, body_start = raw_request.split(b"\r\n\r\n", 1)
            headers_str = headers.decode("utf-8")
            headers_dict = self._parse_headers(headers_str)

            content_length = int(headers_dict.get("Content-Length", 0))
            body = self._receive_body(client_socket, body_start, content_length)

            request = Request((headers + b"\r\n\r\n" + body).decode("utf-8"))
            client_ip, client_port = client_socket.getpeername()
            logger.info(
                f"Parsed request: Method={request.method}, "
                f"Path={request.path}, "
                f"Host={request.headers.get('Host')}, "
                f"Client Address={client_ip}:{client_port}"
            )

            handler = self.router.get_handler(
                request.path, request.method, request.headers.get("Host")
            )
            response = handler(request)

        except FunnelError as e:
            logger.error(
                f"FunnelError: {e.status_code} "
                f"{e.error_reason} - {e.error_message}"
            )
            response = e.to_http_response()
        except Exception as e:
            logger.critical(f"Unexpected error occurred: {e}", exc_info=True)
            error = FunnelError(
                message="An unexpected error occurred.",
                additional_data={"details": str(e)},
            )
            response = error.to_http_response()
        finally:
            logger.info(f"Sending response: Status={response.status_code}")
            client_socket.sendall(response.to_http())
            client_socket.close()
            end_time = time.perf_counter()
            processing_time = end_time - start_time
            logger.info(f"Request processed in {processing_time:.6f} seconds.")


    def _receive_headers(self, client_socket: socket.socket) -> bytes:
        """
        Receive HTTP headers from the client socket until the end of headers marker is found.

        Args:
            client_socket (socket.socket): The client's socket connection.

        Returns:
            bytes: The raw HTTP headers.

        Raises:
            BadRequestError: If the request is empty.
        """
        raw_headers = b""

        while True:
            chunk = client_socket.recv(BUFFER_SIZE)
            if not chunk.strip():
                raise BadRequestError("Empty request received.")
            raw_headers += chunk

            if b"\r\n\r\n" in raw_headers:
                break

        return raw_headers

    def _receive_body(
    self, client_socket: socket.socket, body_start: bytes, content_length: int
) -> bytes:
        """
        Receive the remaining body of the HTTP request.

        Args:
            client_socket (socket.socket): The client's socket connection.
            body_start (bytes): The initial part of the body received with headers.
            content_length (int): The total expected length of the body.

        Returns:
            bytes: The complete body of the HTTP request.

        Raises:
            BadRequestError: If the body is incomplete.
        """
        body = body_start

        while len(body) < content_length:
            chunk = client_socket.recv(BUFFER_SIZE)
            body += chunk

        if len(body) != content_length:
            raise BadRequestError(
                f"Incomplete body received: expected {content_length}, got {len(body)}"
            )

        return body



    def _parse_headers(self, headers_str: str) -> dict:
        """
        Parse raw HTTP headers into a dictionary.

        Args:
            headers_str (str): Raw HTTP headers as a string.

        Returns:
            dict: Parsed headers.
        """
        headers = {}
        for line in headers_str.split("\r\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
        return headers

    def route(
        self, path: str, *, methods: list[str], host: Optional[str] = None
    ) -> Callable:
        """
        Add a route using the Router.

        Args:
            path (str): Path of the route.
            methods (list[str]): Allowed HTTP methods.
            host (Optional[str]): Host of the route.

        Returns:
            Callable: A decorator to register the route.
        """
        return self.router.route(path, methods=methods, host=host)

    def get_mounted_directories(self):
        return list(
            filter(
                lambda x: x is not None,
                [dir.get("directory") for dir in self._mounted_directories],
            )
        )
