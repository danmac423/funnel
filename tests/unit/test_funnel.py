import logging
import signal
import socket
from unittest.mock import MagicMock

import pytest

from funnel.funnel import HTTPServer
from funnel.router import Router


@pytest.fixture
def mock_config(mocker):
    config = {
        "host": "127.0.0.1",
        "port": 8080,
        "max_workers": 5,
    }
    mocker.patch("funnel.funnel.load_config", return_value=config)
    mocker.patch("funnel.funnel.mount_directories")
    return config


class MockedKeyboardInterrupt(Exception):
    """Custom exception to simulate KeyboardInterrupt."""

    pass


@pytest.fixture
def server(mock_config):
    return HTTPServer("mock_config_path")


def test_init(server, mock_config):
    assert server.host == mock_config["host"]
    assert server.port == mock_config["port"]
    assert isinstance(server.router, Router)
    assert server.executor._max_workers == mock_config["max_workers"]
    assert server._running.is_set()


def test_handle_signal(server, mocker):
    mock_stop = mocker.patch.object(server, "stop")
    server._handle_signal(signal.SIGINT, None)
    mock_stop.assert_called_once()


def test_start_stop_server(server, mocker):
    mock_socket = mocker.patch("socket.socket")
    mock_server_socket = MagicMock()
    mock_socket.return_value = mock_server_socket

    mock_accept = mock_server_socket.accept
    mock_accept.side_effect = [
        ("client_socket", ("127.0.0.1", 12345)),
        MockedKeyboardInterrupt,
    ]

    mock_handle_request = mocker.patch.object(server, "_handle_request")
    mock_stop = mocker.patch.object(server, "stop")

    server.start()

    mock_server_socket.bind.assert_called_once_with((server.host, server.port))
    mock_server_socket.listen.assert_called_once_with(256)
    mock_handle_request.assert_called_once_with("client_socket")
    mock_stop.assert_called_once()


def test_stop(server, mocker):
    mock_socket = MagicMock()
    server._server_socket = mock_socket

    mock_executor = MagicMock()
    server.executor = mock_executor

    server.stop()

    assert server._running.is_set() is False
    mock_socket.close.assert_called_once()
    mock_executor.shutdown.assert_called_once_with(wait=True)


def test_handle_request(server, mocker):
    mock_socket = MagicMock()
    mock_socket.recv.return_value = (
        b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )

    mock_request = mocker.patch("funnel.request.Request")
    mock_request.return_value = MagicMock(
        method="GET", path="/", headers={"Host": "localhost"}
    )

    mock_response = mocker.patch("funnel.response.Response")
    mock_response.to_http.return_value = b"HTTP/1.1 200 OK\r\n\r\n"

    mock_router = MagicMock()
    mock_router.get_handler.return_value = MagicMock(
        return_value=mock_response
    )
    mock_socket.getpeername.return_value = ("localhost", 12345)

    server = HTTPServer("mock_config_path")
    server.router = mock_router

    server._handle_request(mock_socket)

    mock_router.get_handler.assert_called_once_with("/", "GET", "localhost")
    mock_socket.sendall.assert_called_once_with(b"HTTP/1.1 200 OK\r\n\r\n")
    mock_socket.close.assert_called_once()


def test_route(server):
    mock_router = MagicMock()
    server.router = mock_router

    route_decorator = server.route("/test", methods=["GET"], host="localhost")
    route_decorator(MagicMock())

    mock_router.route.assert_called_once_with(
        "/test", methods=["GET"], host="localhost"
    )


def test_socket_timeout(server, mocker):
    """Test that the server continues on socket.timeout and stops correctly."""
    mock_socket = mocker.patch("socket.socket")
    mock_server_socket = MagicMock()
    mock_socket.return_value = mock_server_socket

    mock_server_socket.accept.side_effect = [socket.timeout, MagicMock()]
    mock_stop = mocker.patch.object(server, "stop")

    original_running = server._running.is_set

    def stop_running():
        if mock_server_socket.accept.call_count == 2:
            server._running.clear()
        return original_running()

    mocker.patch.object(server._running, "is_set", side_effect=stop_running)

    server.start()

    assert mock_server_socket.accept.call_count == 2

    mock_stop.assert_called_once()


def test_stop_socket_oserror(server, mocker, caplog):
    caplog.set_level(logging.INFO, logger="HTTP Server")

    mock_socket = mocker.patch("socket.socket")
    mock_server_socket = MagicMock()
    mock_socket.return_value = mock_server_socket

    mock_server_socket.close.side_effect = OSError("Test socket error")

    server._server_socket = mock_server_socket

    server.stop()

    assert "Server socket closed." not in caplog.text
    mock_server_socket.close.assert_called_once()


def test_stop_when_already_stopped(server, mocker):
    server._running.clear()

    mock_server_socket = mocker.patch.object(server, "_server_socket")
    mock_executor = mocker.patch.object(server, "executor")

    server.stop()

    mock_server_socket.close.assert_not_called()
    mock_executor.shutdown.assert_not_called()


def test_handle_request_empty_request(server, mocker):
    mock_socket = MagicMock()
    mock_socket.recv.return_value = b"    "

    mock_response = mocker.patch("funnel.response.Response")
    mock_response.return_value.to_http.return_value = (
        b"HTTP/1.1 400 Bad Request\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: 56\r\n\r\n"
        b'{"error": "Empty request received.", "status_code": 400}'
    )
    mock_response.return_value.status_code = 400

    mock_request = mocker.patch("funnel.request.Request")

    server._handle_request(mock_socket)

    mock_request.assert_not_called()
    mock_socket.sendall.assert_called_once_with(
        b"HTTP/1.1 400 Bad Request\r\n"
        b"Content-Type: application/json\r\n"
        b"Content-Length: 56\r\n\r\n"
        b'{"error": "Empty request received.", "status_code": 400}'
    )
    mock_socket.close.assert_called_once()


def test_handle_request_unexpected_error(server, mocker, caplog):
    caplog.set_level(logging.CRITICAL)

    mock_socket = MagicMock()
    mock_socket.recv.return_value = (
        b"GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"
    )
    mock_socket.getpeername.return_value = ("127.0.0.1", 12345)

    mocker.patch.object(
        server.router, "get_handler", side_effect=Exception("Unexpected error")
    )

    mock_response = mocker.patch("funnel.response.Response")
    mock_response.return_value.to_http.return_value = (
        b"HTTP/1.1 500 Internal Server Error\r\nContent-Type: "
        b"application/json\r\nContent-Length: 93\r\n\r\n"
        b'{"error": "An unexpected error occurred.", "status_code": 500, '
        b'"details": "Unexpected error"}'
    )

    server._handle_request(mock_socket)

    mock_socket.sendall.assert_called_once_with(
        b"HTTP/1.1 500 Internal Server Error\r\nContent-Type: "
        b"application/json\r\nContent-Length: 93\r\n\r\n"
        b'{"error": "An unexpected error occurred.", "status_code": 500, '
        b'"details": "Unexpected error"}'
    )

    mock_socket.close.assert_called_once()

    assert "Unexpected error occurred: Unexpected error" in caplog.text


def test_oserror_when_stopped(server, mocker, caplog):
    caplog.set_level(logging.INFO, logger="HTTP Server")

    mock_socket = mocker.patch("socket.socket")
    mock_server_socket = MagicMock()
    mock_socket.return_value = mock_server_socket

    def accept_side_effect():
        server._running.clear()
        raise OSError("Test OSError")

    mock_server_socket.accept.side_effect = accept_side_effect

    mock_stop = mocker.patch.object(server, "stop")

    server._running.set()

    server.start()

    assert "Server socket has been closed." in caplog.text
    assert "Socket error: Test OSError" not in caplog.text
    mock_stop.assert_called_once()


def test_oserror_when_running(server, mocker, caplog):
    caplog.set_level(logging.ERROR, logger="HTTP Server")

    mock_socket = mocker.patch("socket.socket")
    mock_server_socket = MagicMock()
    mock_socket.return_value = mock_server_socket

    mock_server_socket.accept.side_effect = [
        OSError("Test OSError"),
        MagicMock(),
    ]

    server._running.set()

    original_running = server._running.is_set

    def stop_running():
        if mock_server_socket.accept.call_count == 2:
            server._running.clear()
        return original_running()

    mocker.patch.object(server._running, "is_set", side_effect=stop_running)

    server.start()

    assert "Socket error: Test OSError" in caplog.text
    assert mock_server_socket.accept.call_count == 2


def test_get_mounted_directories_empty(server):
    """
    Test when no directories are mounted.
    """
    server._mounted_directories = []
    result = server.get_mounted_directories()
    assert result == []


def test_get_mounted_directories_valid(server):
    """
    Test when directories are correctly configured.
    """
    server._mounted_directories = [
        {"directory": "/var/www/html"},
        {"directory": "/mnt/data"},
    ]
    result = server.get_mounted_directories()
    assert result == ["/var/www/html", "/mnt/data"]


def test_get_mounted_directories_missing_key(server):
    """
    Test when some mounted directories have missing 'directory' keys.
    """
    server._mounted_directories = [
        {"directory": "/var/www/html"},
        {"invalid_key": "/mnt/data"},
    ]
    result = server.get_mounted_directories()
    assert result == ["/var/www/html"]


def test_get_mounted_directories_none_directory(server):
    """
    Test when 'directory' key exists but has a None value.
    """
    server._mounted_directories = [
        {"directory": "/var/www/html"},
        {"directory": None},
    ]
    result = server.get_mounted_directories()
    assert result == ["/var/www/html"]
