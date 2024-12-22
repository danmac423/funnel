import socket
from typing import Callable

from funnel.request import Request
from funnel.router import Router
from funnel.exceptions import FunnelError


class HTTPServer:
    """
    A basic HTTP server supporting configuration,
    routing, and request handling.
    """

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.router = Router()

    def start(self) -> None:
        """
        Start the HTTP server and listen for incoming requests.
        """
        print(f"Starting server on {self.host}:{self.port}...")
        with socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        ) as server_socket:
            server_socket.bind((self.host, self.port))
            server_socket.listen(5)
            print(f"Server is running on http://{self.host}:{self.port}")
            while True:
                client_socket, _ = server_socket.accept()
                with client_socket:
                    self._handle_request(client_socket)

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
            handler = self.router.get_handler(request.path, request.method)
            response = handler(request)

        except FunnelError as e:
            response = e.to_http_response()
        except Exception as e:
            error = FunnelError(
                message="An unexpected error occurred.",
                additional_data={"details": str(e)},
            )
            response = error.to_http_response()

        client_socket.sendall(response.to_http().encode("utf-8"))

    def route(self, path: str, methods: list[str]) -> Callable:
        """
        Add a route using the Router.

        Args:
            path (str): Path of the route.
            methods (list[str]): Allowed HTTP methods.

        Returns:
            Callable: A decorator to register the route.
        """
        return self.router.route(path, methods)
