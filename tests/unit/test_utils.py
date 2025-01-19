import os
from unittest.mock import MagicMock, patch

import pytest

from funnel.exceptions import BadRequestError, MethodNotAllowedError, NotFoundError
from funnel.request import Request
from funnel.router import Router
from funnel.utils import (
    delete_file,
    directory_handler_factory,
    load_config,
    mount_directories,
    resolve_requested_path,
    save_json_file,
    serve_directory,
    serve_file,
)


class MockServer:
    def __init__(self, tmp_path):
        self._mounted_directories = [{"directory": f"{tmp_path}"}]

    def get_mounted_directories(self):
        return [dir.get("directory") for dir in self._mounted_directories]


def create_mock_request(path: str) -> Request:
    raw_request = f"GET {path} HTTP/1.1\r\nHost: localhost\r\n\r\n"
    return Request(raw_request)


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
    assert config["mounted_directories"] == [{"path": "/static", "directory": "/etc"}]


def test_load_config_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError, match="Configuration file not found:"):
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

    resolved_path = resolve_requested_path(request_path, base_path, base_directory)
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
    with patch("os.listdir", side_effect=OSError("Test error")):
        with pytest.raises(NotFoundError) as excinfo:
            serve_directory(str(tmp_path), "/static")

        assert "Error reading folder" in str(excinfo.value)
        assert str(tmp_path) in str(excinfo.value)


def test_serve_file_valid(tmp_path):
    file = tmp_path / "file.txt"
    file.write_text("Hello, World!")

    request = create_mock_request(file)

    response = serve_file(str(file), request)
    assert response.status_code == 200
    assert response.body == b"Hello, World!"
    assert response.headers["Content-Type"] == "text/plain"


def test_serve_file_binary(tmp_path):
    file = tmp_path / "image.jpg"
    file.write_bytes(b"binary content")

    request = create_mock_request(file)

    response = serve_file(str(file), request)
    assert response.status_code == 200
    assert response.body == b"binary content"
    assert response.headers["Content-Type"] == "image/jpeg"


def test_serve_file_non_standard(tmp_path):
    file = tmp_path / "file.non_standard"
    file.write_text("Hello, World!")

    request = create_mock_request(file)

    response = serve_file(str(file), request)
    assert response.status_code == 200
    assert response.body == b"Hello, World!"
    assert response.headers["Content-Type"] == "application/octet-stream"


def test_serve_file_read_error(tmp_path, mocker):
    file = tmp_path / "file.txt"
    file.write_text("content")

    request = create_mock_request(str(file))

    with patch("builtins.open", side_effect=OSError("Read error")):
        with pytest.raises(BadRequestError, match="Error reading file:"):
            serve_file(str(file), request)


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


def test_directory_handler_post_valid_json(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    request = MagicMock()
    request.method = "POST"
    request.path = "/static"
    request.headers = {"Content-Type": "application/json"}
    request.parsed_body = {"key": "value"}
    request.query_params = {"filename": "test.json"}

    handler = directory_handler_factory(str(subdir), "/static")
    response = handler(request)

    assert response.status_code == 201
    assert "File uploaded successfully" in response.body
    assert subdir.joinpath("test.json").exists()


def test_directory_handler_post_valid_json_no_filename(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    request = MagicMock()
    request.method = "POST"
    request.path = "/static"
    request.headers = {"Content-Type": "application/json"}
    request.parsed_body = {"key": "value"}
    request.query_params = {}

    handler = directory_handler_factory(str(subdir), "/static")
    with patch("time.time", return_value=123):
        response = handler(request)

    assert response.status_code == 201
    assert "File uploaded successfully" in response.body
    assert subdir.joinpath("upload_123.json").exists()


def test_directory_handler_post_nonexistent_directory(tmp_path):
    request = MagicMock()
    request.method = "POST"
    request.path = "/static/nonexistent"
    request.headers = {"Content-Type": "application/json"}
    request.parsed_body = {"key": "value"}
    request.query_params = {}

    handler = directory_handler_factory(str(tmp_path), "/static")

    with pytest.raises(NotFoundError, match="Directory not found."):
        handler(request)


def test_directory_handler_not_supported_method(tmp_path):
    request = MagicMock()
    request.method = "UNSUPPORTED"
    request.path = "/static"
    request.headers = {"Content-Type": "application/json"}
    request.parsed_body = {"key": "value"}
    request.query_params = {}

    handler = directory_handler_factory(str(tmp_path), "/static")

    with pytest.raises(MethodNotAllowedError, match="Method UNSUPPORTED not supported."):
        handler(request)


def test_save_json_file_wrong_content_type(tmp_path):
    request = MagicMock()
    request.method = "POST"
    request.path = "/static"
    request.headers = {"Content-Type": "application/not_json"}
    request.parsed_body = {"key": "value"}
    request.query_params = {}

    with pytest.raises(BadRequestError, match="Only JSON files are allowed"):
        save_json_file(request, "/static")


def test_save_json_file_not_json(tmp_path):
    request = MagicMock()
    request.method = "POST"
    request.path = "/static"
    request.headers = {"Content-Type": "application/json"}
    request.parsed_body = "json"
    request.query_params = {}

    with pytest.raises(BadRequestError, match="Invalid JSON data."):
        save_json_file(request, "/static")


def test_save_json_file_filename_not_json(tmp_path):
    request = MagicMock()
    request.method = "POST"
    request.path = "/static"
    request.headers = {"Content-Type": "application/json"}
    request.parsed_body = {"json": 12}
    request.query_params = {"filename": "test.txt"}

    with pytest.raises(BadRequestError, match="Invalid filename. Must be a valid JSON filename."):
        save_json_file(request, "/static")


def test_serve_file_with_range_full_file(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello, this is a test file!")

    request = MagicMock()
    request.headers = {}

    response = serve_file(str(file_path), request)

    assert response.status_code == 200
    assert response.headers["Content-Length"] == str(file_path.stat().st_size)
    assert response.body == b"Hello, this is a test file!"


def test_serve_file_with_range_partial(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello, this is a test file!")

    request = MagicMock()
    request.headers = {"Range": "bytes=7-20"}

    response = serve_file(str(file_path), request)

    assert response.status_code == 206
    assert response.headers["Content-Range"] == "bytes 7-20/27"
    assert response.body == b"this is a test"


def test_serve_file_with_range_invalid_range(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello, this is a test file!")

    request = MagicMock()
    request.headers = {"Range": "bytes=50-60"}

    with pytest.raises(BadRequestError, match="Invalid byte range."):
        serve_file(str(file_path), request)


def test_serve_file_with_range_header_format(tmp_path):
    file_path = tmp_path / "test.txt"
    file_path.write_text("Hello, this is a test file!")

    request = MagicMock()
    request.headers = {"Range": "bytes="}

    with pytest.raises(BadRequestError, match="Invalid Range header format."):
        serve_file(str(file_path), request)


def test_serve_file_with_range_no_file():
    non_existent_file_path = "/path/to/non_existent_file.txt"

    request = MagicMock()
    request.headers = {"Range": "bytes=1-10"}

    with pytest.raises(NotFoundError, match=f"File not found: {non_existent_file_path}"):
        serve_file(non_existent_file_path, request)


def test_directory_handler_delete_existing_file(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()
    file_to_delete = subdir / "file.json"
    file_to_delete.write_text("{}")

    request = MagicMock()
    request.method = "DELETE"
    request.path = "/static/file.json"

    handler = directory_handler_factory(str(subdir), "/static")
    response = handler(request)

    assert response.status_code == 200
    assert "deleted successfully" in response.body
    assert not file_to_delete.exists()


def test_directory_handler_delete_nonexistent_file(tmp_path):
    subdir = tmp_path / "subdir"
    subdir.mkdir()

    request = MagicMock()
    request.method = "DELETE"
    request.path = "/static/nonexistent.json"

    handler = directory_handler_factory(str(subdir), "/static")

    with pytest.raises(NotFoundError):
        handler(request)


def test_delete_file_success(tmp_path):
    file_path = tmp_path / "test_delete.json"
    file_path.write_text("{}")

    response = delete_file(str(file_path))

    assert response.status_code == 200
    assert "deleted successfully" in response.body
    assert not file_path.exists()


def test_delete_file_not_found(tmp_path):
    file_path = tmp_path / "nonexistent.json"

    with pytest.raises(NotFoundError, match=f"File not found: {file_path}"):
        delete_file(str(file_path))


def test_delete_file_permission_error_mock(tmp_path):
    file_path = tmp_path / "test_delete.json"
    file_path.write_text("Test content")

    with patch("os.remove", side_effect=OSError("Permission denied")):
        with pytest.raises(BadRequestError, match="Error deleting file:"):
            delete_file(str(file_path))
