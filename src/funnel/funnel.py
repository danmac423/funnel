import socket
import signal
import sys
import os
import logging
import threading

from logging.handlers import RotatingFileHandler
from typing import Callable, Optional
from concurrent.futures import ThreadPoolExecutor


from funnel.request import Request
from funnel.router import Router
from funnel.exceptions import FunnelError
from funnel.utils import load_config, directory_handler_factory

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
        logger.info("Router initialized")
        self.executor = ThreadPoolExecutor(
            max_workers=config.get("max_workers", 10)
        )
        self._running = threading.Event()
        self._running.set()

        self._server_socket = None

        self._mount_directories(config)

        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

    def _handle_signal(self, sig, _) -> None:
        """
        Handle a signal to stop the server.
        """
        print(f"\nReceived signal {sig}. Stopping server...")
        self.stop()

    def _mount_directories(self, config):
        """
        Mount directries given in cofing file.
        """
        mount: dict
        for mount in config.get("mounted_directories", []):
            base_path = mount.get("path")
            root_directory = mount.get("directory")

            if not base_path or not root_directory:
                raise ValueError(
                    "Each mount must specify 'path' and 'directory'."
                )

            base_path = os.path.normpath(base_path)
            root_directory = os.path.abspath(root_directory)

            for current_dir, sub_dirs, files in os.walk(root_directory):
                relative_path = os.path.relpath(current_dir, root_directory)

                url_path = os.path.normpath(f"{base_path}/{relative_path}")
                self.router._add_route(
                    path=url_path,
                    methods=["GET"],
                    handler=directory_handler_factory(current_dir),
                )

                for file in files:
                    file_path = os.path.normpath(f"{url_path}/{file}")
                    self.router._add_route(
                        path=file_path,
                        methods=["GET"],
                        handler=directory_handler_factory(
                            os.path.join(current_dir, file)
                        ),
                    )

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
        Handle an incoming HTTP request.

        Args:
            client_socket (socket.socket): The client's socket connection.
        """
        try:
            raw_request = client_socket.recv(1024).decode("utf-8")
            if not raw_request.strip():
                return

            request = Request(raw_request)
            logger.info(
                f"Parsed request: Method={request.method}, "
                f"Path={request.path}, "
                f"Host={request.headers.get('Host')}"
            )

            handler = self.router.get_handler(
                request.path, request.method, request.headers.get("Host")
            )
            response = handler(request)

        except FunnelError as e:
            logger.error(f"FunnelError: {e}")
            response = e.to_http_response()
        except Exception as e:
            logger.critical(f"Unexpected error occurred: {e}", exc_info=True)
            error = FunnelError(
                message="An unexpected error occurred.",
                additional_data={"details": str(e)},
            )
            response = error.to_http_response()
        finally:
            logger.info(f"Sending response:  Status={response.status_code}")
            client_socket.sendall(response.to_http().encode("utf-8"))
            client_socket.close()

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
