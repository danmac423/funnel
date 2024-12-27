import pytest
import os

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


def test_valid_load_config_host(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(VALID_CONFIG, encoding="utf-8")

    config = load_config(p)

    host = config.get("host", "127.0.0.1")

    assert p.read_text(encoding="utf-8") == VALID_CONFIG
    assert host == "127.0.0.2"


def test_invalid_load_config_host(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(EMPTY_CONFIG, encoding="utf-8")

    config = load_config(p)

    host = config.get("host", "127.0.0.1")

    assert p.read_text(encoding="utf-8") == EMPTY_CONFIG
    assert host == "127.0.0.1"


def test_valid_load_config_port(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(VALID_CONFIG, encoding="utf-8")

    config = load_config(p)

    port = config.get("port", 8080)

    assert p.read_text(encoding="utf-8") == VALID_CONFIG
    assert port == 8081


def test_invalid_load_config_port(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(EMPTY_CONFIG, encoding="utf-8")

    config = load_config(p)

    port = config.get("port", 8080)

    assert p.read_text(encoding="utf-8") == EMPTY_CONFIG
    assert port == 8080


def test_valid_load_config_workers(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(VALID_CONFIG, encoding="utf-8")

    config = load_config(p)

    max_workers = config.get("max_workers", 10)

    assert p.read_text(encoding="utf-8") == VALID_CONFIG
    assert max_workers == 11


def test_invalid_load_config_workers(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(EMPTY_CONFIG, encoding="utf-8")

    config = load_config(p)

    max_workers = config.get("max_workers", 10)

    assert p.read_text(encoding="utf-8") == EMPTY_CONFIG
    assert max_workers == 10


def test_valid_load_config_mounted_directories(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(VALID_CONFIG, encoding="utf-8")

    config = load_config(p)

    mounted_directories = config.get("mounted_directories", [])

    assert p.read_text(encoding="utf-8") == VALID_CONFIG
    assert mounted_directories[0] == {"directory": "/etc/", "path": "/static"}
    assert mounted_directories[1] == {
        "directory": "/home/",
        "path": "/uploads",
    }


def test_invalid_load_config_mounted_directories(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(EMPTY_CONFIG, encoding="utf-8")

    config = load_config(p)

    mounted_directories = config.get("mounted_directories", [])

    assert p.read_text(encoding="utf-8") == EMPTY_CONFIG
    assert mounted_directories == []


def test_invalid_load_config_dir_path(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(EMPTY_CONFIG, encoding="utf-8")

    with pytest.raises(IsADirectoryError) as excinfo:
        config = load_config(d)
    assert "is a directory" in str(excinfo.value)


def test_invalid_load_config_wrong_path(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(EMPTY_CONFIG, encoding="utf-8")

    with pytest.raises(FileNotFoundError) as excinfo:
        config = load_config(d / "wrong_file.yaml")
    assert "Configuration file not found:" in str(excinfo.value)


def test_invalid_load_config_invalid_yaml(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "config.yaml"
    p.write_text(INVALID_CONFIG, encoding="utf-8")

    with pytest.raises(ValueError) as excinfo:
        config = load_config(p)
    assert "Error parsing YAML file:" in str(excinfo.value)


def test_handler_factory_directory(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(EMPTY_CONFIG, encoding="utf-8")

    handler = directory_handler_factory(d)
    response = handler(None)

    assert p.read_text(encoding="utf-8") == EMPTY_CONFIG
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "text/html"
    assert "hello.txt" in response.body


def test_handler_factory_file(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(EMPTY_CONFIG, encoding="utf-8")

    handler = directory_handler_factory(p)
    response = handler(None)

    assert p.read_text(encoding="utf-8") == EMPTY_CONFIG
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/octet-stream"


def test_handler_factory_wrong_path(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(EMPTY_CONFIG, encoding="utf-8")

    handler = directory_handler_factory(d / "wrong_file.yaml")
    with pytest.raises(NotFoundError) as excinfo:
        response = handler(None)
    assert "File or directory not found:" in str(excinfo.value)
