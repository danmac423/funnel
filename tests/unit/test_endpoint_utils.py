import json
from unittest.mock import MagicMock, patch

import pytest

from funnel.endpoint_utils import remove_file, save_json
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


def test_save_json_correct(tmp_path):
    """
    Test saving a valid JSON file.
    """
    file_path = str(tmp_path / "data.json")
    server = MockServer(tmp_path=tmp_path)

    body = json.dumps({"key": "value"})
    request = create_mock_request(path=file_path, body=body)

    save_json(server, request)

    # Weryfikacja zapisanego pliku
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data == {"key": "value"}


def test_save_json_missing_path(tmp_path):
    """
    Test missing 'path' query parameter.
    """
    server = MockServer(tmp_path=tmp_path)
    request = create_mock_request(path=None, body='{"key": "value"}')

    with pytest.raises(BadRequestError, match="Missing 'path' query parameter."):
        save_json(server, request)


def test_save_json_invalid_path(tmp_path):
    """
    Test saving to a path outside mounted directories.
    """
    server = MockServer(tmp_path=tmp_path)
    invalid_path = "/invalid/path/data.json"
    request = create_mock_request(path=invalid_path, body='{"key": "value"}')

    with pytest.raises(BadRequestError, match="Target path is not within a mounted directory."):
        save_json(server, request)


def test_save_json_empty_body(tmp_path):
    """
    Test with an empty request body.
    """
    file_path = str(tmp_path / "data.json")
    server = MockServer(tmp_path=tmp_path)
    request = create_mock_request(path=file_path, body=None)

    with pytest.raises(BadRequestError, match="Request body is empty."):
        save_json(server, request)


def test_save_json_invalid_json_format(tmp_path):
    """
    Test with invalid JSON format in the body.
    """
    file_path = str(tmp_path / "data.json")
    server = MockServer(tmp_path=tmp_path)
    request = create_mock_request(path=file_path, body="invalid json")

    with pytest.raises(BadRequestError, match="Invalid JSON format: .*"):
        save_json(server, request)


def test_save_json_file_write_error(tmp_path):
    """
    Test handling file write errors.
    """
    file_path = str(tmp_path / "data.json")
    server = MockServer(tmp_path=tmp_path)
    body = json.dumps({"key": "value"})
    request = create_mock_request(path=file_path, body=body)

    # Patchowanie `open` tak, aby zgłaszało `OSError`
    with patch("builtins.open", side_effect=OSError("Test error")):
        with pytest.raises(BadRequestError, match="Failed to save file: Test error"):
            save_json(server, request)