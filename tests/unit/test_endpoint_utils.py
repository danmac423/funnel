from unittest.mock import MagicMock

import pytest

from funnel.endpoint_utils import remove_file
from funnel.exceptions import BadRequestError, NotFoundError
from funnel.funnel import HTTPServer
from funnel.request import Request


class MockServer(HTTPServer):
    def __init__(self, tmp_path):
        self._mounted_directories = [{"directory": f'{tmp_path}'}]

    def get_mounted_directories(self):
        return [dir.get("directory") for dir in self._mounted_directories]


def create_mock_del_request(path: str, file_path: str) -> Request:
    raw_request = (
        f"DELETE {path} HTTP/1.1\r\n"
        "Host: localhost:8080\r\n"
        "Content-Type: application/json\r\n"
        f"Content-Length: {12+len(file_path)}\r\n\r\n"
        f'{{"path": "{file_path}"}}'
    )
    request = Request(raw_request)
    return request

def create_mock_request(path, body=None):
    query_params = {"path": path}
    raw_body = body if body else None
    request = MagicMock()
    request.query_params = query_params
    request.body = raw_body
    return request


def test_remove_file_correct(tmp_path):
    file_path = tmp_path / "del.txt"
    open(file_path, 'a').close()

    request = create_mock_del_request("/data", "del.txt")
    server = MockServer(tmp_path=tmp_path)
    remove_file(server=server, request=request)

def test_remove_file_not_found(tmp_path):
    request = create_mock_del_request("/data", "del.txt")
    server = MockServer(tmp_path=tmp_path)
    with pytest.raises(NotFoundError):
        remove_file(server=server, request=request)

def test_remove_file_wrong_path(tmp_path):
    file_path = tmp_path / "del.txt"
    open(file_path, 'a').close()

    request = create_mock_del_request("/data", "example/del.txt")
    server = MockServer(tmp_path=tmp_path)
    with pytest.raises(NotFoundError):
        remove_file(server=server, request=request)

def test_remove_file_forbidden_path(tmp_path):
    file_path = tmp_path / "../del.txt"
    open(file_path, 'a').close()

    request = create_mock_del_request("/data", "../del.txt")
    server = MockServer(tmp_path=tmp_path)
    with pytest.raises(NotFoundError):
        remove_file(server=server, request=request)

def test_remove_file_missing_body(tmp_path):
    raw_request = (
        "DELETE /data HTTP/1.1\r\n"
        "Host: localhost:8080\r\n"
        "Content-Type: application/json\r\n\r\n"
    )
    request = Request(raw_request)

    server = MockServer(tmp_path=tmp_path)
    with pytest.raises(BadRequestError):
        remove_file(server=server, request=request)
