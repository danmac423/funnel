import os
from unittest.mock import patch

import pytest

from funnel.exceptions import NotFoundError
from funnel.request import Request
from funnel.router import Router
from funnel.utils import (
    directory_handler_factory,
    load_config,
    mount_directories,
    resolve_requested_path,
    serve_directory,
    serve_file,
    remove_file
)

class MockServer():
    def __init__(self, tmp_path):
        self._mounted_directories = [{"directory": f'{tmp_path}'}]

    def get_mounted_directories(self):
        return [dir.get("directory") for dir in self._mounted_directories]

def create_mock_request(path: str) -> Request:
    raw_request = f"GET {path} HTTP/1.1\r\nHost: localhost\r\n\r\n"
    return Request(raw_request)

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


def test_load_config_valid(tmp_path):
    config_content = """
    host: "127.0.0.1"
    port: 8080
    mounted_directories:
      - path: "/static"
        directory: "/etc"
    """
    config_file = tmp_path / "config.yaml"
    config_file.write_text(config_content, encoding="utf-8")
    config = load_config(config_file)

    assert config["host"] == "127.0.0.1"
    assert config["port"] == 8080
    assert config["mounted_directories"] == [
        {"path": "/static", "directory": "/etc"}
    ]


def test_load_config_file_not_found(tmp_path):
    with pytest.raises(
        FileNotFoundError, match="Configuration file not found:"
    ):
        load_config(tmp_path / "missing.yaml")


def test_load_config_is_directory(tmp_path):
    with pytest.raises(IsADirectoryError, match="is a directory"):
        load_config(tmp_path)


def test_load_config_invalid_yaml(tmp_path):
    config_file = tmp_path / "invalid.yaml"
    config_file.write_text("invalid_yaml_content: [", encoding="utf-8")
    with pytest.raises(ValueError, match="Error parsing YAML file:"):
        load_config(config_file)


def test_mount_directories_valid(tmp_path):
    router = Router()

    mock_static_dir = tmp_path / "static"
    mock_static_dir.mkdir()
    (mock_static_dir / "file.txt").write_text("content")

    config = {
        "mounted_directories": [
            {"path": "/static", "directory": str(mock_static_dir)},
        ]
    }

    mount_directories(router, config)

    handler = router.get_handler("/static/file.txt", "GET")
    assert callable(handler)

    request = create_mock_request("/static/file.txt")
    response = handler(request)
    assert response.status_code == 200
    assert response.body == b"content"


def test_mount_directories_invalid_config():
    router = Router()
    invalid_config = {"mounted_directories": [{"path": "/static"}]}

    with pytest.raises(TypeError):
        mount_directories(router, invalid_config)


def test_resolve_requested_path_valid():
    base_directory = "/base"
    base_path = "/static"
    request_path = "/static/subdir/file.txt"

    resolved_path = resolve_requested_path(
        request_path, base_path, base_directory
    )
    assert resolved_path == os.path.normpath("/base/subdir/file.txt")


def test_resolve_requested_path_traversal():
    base_directory = "/base"
    base_path = "/static"
    request_path = "/static/../etc/passwd"

    with pytest.raises(NotFoundError, match="Path not found."):
        resolve_requested_path(request_path, base_path, base_directory)


def test_serve_directory(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file1.txt").write_text("content1")
    (subdir / "file2.txt").write_text("content2")

    response = serve_directory(str(subdir), "/static")
    assert response.status_code == 200
    assert "file1.txt" in str(response.body)
    assert "file2.txt" in str(response.body)


def test_serve_directory_exception(tmp_path):
    # Mock os.listdir to raise an exception
    with patch("os.listdir", side_effect=OSError("Test error")):
        with pytest.raises(NotFoundError) as excinfo:
            serve_directory(str(tmp_path), "/static")

        # Assert the exception message
        assert "Error reading folder" in str(excinfo.value)
        assert str(tmp_path) in str(excinfo.value)


def test_serve_file_valid(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("Hello, World!")

    response = serve_file(str(file))
    assert response.status_code == 200
    assert response.body == b"Hello, World!"
    assert response.headers["Content-Type"] == "text/plain"


def test_serve_file_binary(tmp_path):
    file = tmp_path / "image.jpg"
    file.write_bytes(b"binary content")

    response = serve_file(str(file))
    assert response.status_code == 200
    assert response.body == b"binary content"
    assert response.headers["Content-Type"] == "image/jpeg"


def test_serve_file_non_standard(tmp_path):
    file = tmp_path / "file.non_standard"
    file.write_text("Hello, World!")

    response = serve_file(str(file))
    assert response.status_code == 200
    assert response.body == b"Hello, World!"
    assert response.headers["Content-Type"] == "application/octet-stream"


def test_serve_file_read_error(tmp_path, mocker):
    file = tmp_path / "file.txt"
    file.write_text("content")

    mocker.patch("builtins.open", side_effect=OSError("Read error"))

    with pytest.raises(NotFoundError, match="Error reading file:"):
        serve_file(str(file))


def test_directory_handler_factory_for_directory(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    (subdir / "file1.txt").write_text("content1")
    (subdir / "file2.txt").write_text("content2")

    handler = directory_handler_factory(str(subdir), "/static")
    request = create_mock_request("/static")
    response = handler(request)

    assert response.status_code == 200
    assert "file1.txt" in response.body
    assert "file2.txt" in response.body


def test_directory_handler_factory_for_file(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("Hello, World!")

    with pytest.raises(ValueError, match="Base directory not found: "):
        directory_handler_factory(str(file), "/static")


def test_directory_handler_factory_not_found(tmp_path):
    handler = directory_handler_factory(str(tmp_path), "/static")
    request = create_mock_request("/static/nonexistent")

    with pytest.raises(NotFoundError, match="File or directory not found."):
        handler(request)


def test_directory_handler_factory_nonexistent_path(tmp_path):
    nonexistent_path = tmp_path / "nonexistent"
    with pytest.raises(ValueError):
        directory_handler_factory(str(nonexistent_path), "/static")


def test_remove_file_correct(tmp_path):
    file_path = tmp_path / "del.txt"
    open(file_path, 'a').close()

    request = create_mock_del_request("/data", "del.txt")
    server = MockServer(tmp_path=tmp_path)
    remove_file(server=server, request=request)
