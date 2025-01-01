import pytest

from funnel.request import Request
from funnel.utils import directory_handler_factory, load_config
from funnel.exceptions import NotFoundError

VALID_CONFIG = """
host: "127.0.0.2"
port: 8081
max_workers: 11
mounted_directories:
  - path: "/static"
    directory: "/etc/"
  - path: "/uploads"
    directory: "/home/"
"""
EMPTY_CONFIG = "a: 0"
INVALID_CONFIG = "aaa: ][]"


def create_mock_request(path: str) -> Request:
    raw_request = f"GET {path} HTTP/1.1\r\nHost: localhost\r\n\r\n"
    return Request(raw_request)


def test_load_config_valid(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(VALID_CONFIG, encoding="utf-8")
    config = load_config(config_file)
    assert config["host"] == "127.0.0.2"
    assert config["port"] == 8081
    assert config["max_workers"] == 11
    assert config["mounted_directories"] == [
        {"path": "/static", "directory": "/etc/"},
        {"path": "/uploads", "directory": "/home/"},
    ]


def test_load_config_empty(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(EMPTY_CONFIG, encoding="utf-8")
    config = load_config(config_file)

    assert config == {"a": 0}


def test_load_config_file_not_found(tmp_path):
    config_file = tmp_path / "missing_config.yaml"
    with pytest.raises(
        FileNotFoundError, match="Configuration file not found:"
    ):
        load_config(config_file)


def test_load_config_is_directory(tmp_path):
    with pytest.raises(IsADirectoryError, match="is a directory"):
        load_config(tmp_path)


def test_load_config_invalid_yaml(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text(INVALID_CONFIG, encoding="utf-8")
    with pytest.raises(ValueError, match="Error parsing YAML file:"):
        load_config(config_file)


def test_directory_handler_factory_directory(tmp_path):
    subdir = tmp_path / "sub"
    subdir.mkdir()
    file1 = subdir / "file1.txt"
    file1.write_text("content1", encoding="utf-8")
    file2 = subdir / "file2.txt"
    file2.write_text("content2", encoding="utf-8")

    handler = directory_handler_factory(str(subdir))
    request = create_mock_request(str(subdir))
    response = handler(request)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/html"
    assert "file1.txt" in response.body
    assert "file2.txt" in response.body


def test_directory_handler_factory_html_file(tmp_path):
    txt_file = tmp_path / "file.html"
    txt_file.write_text("html file content", encoding="utf-8")

    handler = directory_handler_factory(str(txt_file))
    request = create_mock_request(str(txt_file))
    response = handler(request)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/html"
    assert response.body == b"html file content"


def test_directory_handler_factory_text_file(tmp_path):
    txt_file = tmp_path / "file.txt"
    txt_file.write_text("txt file content", encoding="utf-8")

    handler = directory_handler_factory(str(txt_file))
    request = create_mock_request(str(txt_file))
    response = handler(request)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/plain"
    assert response.body == b"txt file content"


def test_directory_handler_factory_jpg_file(tmp_path):
    jpg_file = tmp_path / "file.jpg"
    jpg_file.write_bytes(b"jpg file content")

    handler = directory_handler_factory(str(jpg_file))
    request = create_mock_request(str(jpg_file))
    response = handler(request)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/jpeg"
    assert response.body == b"jpg file content"


def test_directory_handler_factory_png_file(tmp_path):
    png_file = tmp_path / "file.png"
    png_file.write_bytes(b"png file content")

    handler = directory_handler_factory(str(png_file))
    request = create_mock_request(str(png_file))
    response = handler(request)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "image/png"
    assert response.body == b"png file content"


def test_directory_handler_factory_non_standard_file(tmp_path):
    png_file = tmp_path / "file.non-standard"
    png_file.write_bytes(b"non-standard file content")

    handler = directory_handler_factory(str(png_file))
    request = create_mock_request(str(png_file))
    response = handler(request)

    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/octet-stream"
    assert response.body == b"non-standard file content"


def test_directory_handler_factory_nonexistent_path_with_request(tmp_path):
    nonexistent_path = tmp_path / "nonexistent"
    handler = directory_handler_factory(str(nonexistent_path))
    request = create_mock_request(str(nonexistent_path))
    with pytest.raises(NotFoundError, match="File or directory not found:"):
        handler(request)


def test_directory_handler_factory_file_read_error_with_request(
    tmp_path, mocker
):
    file = tmp_path / "file.txt"
    file.write_text("content", encoding="utf-8")

    mocker.patch("builtins.open", side_effect=OSError("Read error"))

    handler = directory_handler_factory(str(file))
    request = create_mock_request(str(file))

    with pytest.raises(NotFoundError, match="Error reading file:"):
        handler(request)
