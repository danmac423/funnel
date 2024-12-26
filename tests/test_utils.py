import pytest

from funnel.utils import directory_handler_factory, load_config

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
INVALID_CONFIG = "a: 0"


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
    p.write_text(INVALID_CONFIG, encoding="utf-8")

    config = load_config(p)

    host = config.get("host", "127.0.0.1")

    assert p.read_text(encoding="utf-8") == INVALID_CONFIG
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
    p.write_text(INVALID_CONFIG, encoding="utf-8")

    config = load_config(p)

    port = config.get("port", 8080)

    assert p.read_text(encoding="utf-8") == INVALID_CONFIG
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
    p.write_text(INVALID_CONFIG, encoding="utf-8")

    config = load_config(p)

    max_workers = config.get("max_workers", 10)

    assert p.read_text(encoding="utf-8") == INVALID_CONFIG
    assert max_workers == 10


def test_invalid_load_config_workers(tmp_path):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "hello.txt"
    p.write_text(INVALID_CONFIG, encoding="utf-8")

    config = load_config(p)

    max_workers = config.get("max_workers", 10)

    assert p.read_text(encoding="utf-8") == INVALID_CONFIG
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
    p.write_text(INVALID_CONFIG, encoding="utf-8")

    config = load_config(p)

    mounted_directories = config.get("mounted_directories", [])

    assert p.read_text(encoding="utf-8") == INVALID_CONFIG
    assert mounted_directories == []
