import pytest

from funnel.exceptions import BadRequestError
from funnel.request import Request


def test_valid_get_request():
    raw_request = (
        "GET /api/resource?key=value HTTP/1.1\r\n"
        "Host: localhost:8080\r\n"
        "User-Agent: TestClient\r\n\r\n"
    )
    request = Request(raw_request)

    assert request.method == "GET"
    assert request.path == "/api/resource"
    assert request.protocol == "HTTP/1.1"
    assert request.headers == {
        "Host": "localhost:8080",
        "User-Agent": "TestClient",
    }
    assert request.query_params == {"key": "value"}
    assert request.body is None
    assert request.parsed_body is None


def test_valid_post_request_with_json():
    raw_request = (
        "POST /api/resource HTTP/1.1\r\n"
        "Host: localhost:8080\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: 27\r\n\r\n"
        '{"key": "value", "test": 1}'
    )
    request = Request(raw_request)

    assert request.method == "POST"
    assert request.path == "/api/resource"
    assert request.protocol == "HTTP/1.1"
    assert request.headers == {
        "Host": "localhost:8080",
        "Content-Type": "application/json",
        "Content-Length": "27",
    }
    assert request.body == '{"key": "value", "test": 1}'
    assert request.parsed_body == {"key": "value", "test": 1}


def test_valid_post_request_with_form_data():
    raw_request = (
        "POST /submit-form HTTP/1.1\r\n"
        "Host: localhost:8080\r\n"
        "Content-Type: application/x-www-form-urlencoded\r\n"
        "Content-Length: 20\r\n\r\n"
        "username=test&age=30"
    )
    request = Request(raw_request)

    assert request.method == "POST"
    assert request.path == "/submit-form"
    assert request.protocol == "HTTP/1.1"
    assert request.headers == {
        "Host": "localhost:8080",
        "Content-Type": "application/x-www-form-urlencoded",
        "Content-Length": "20",
    }
    assert request.body == "username=test&age=30"
    assert request.parsed_body == {"username": "test", "age": "30"}


def test_invalid_request_line():
    raw_request = "INVALID_REQUEST_LINE"
    with pytest.raises(BadRequestError, match="Invalid request line."):
        Request(raw_request)


def test_missing_host_header():
    raw_request = (
        "GET /api/resource HTTP/1.1\r\nUser-Agent: TestClient\r\n\r\n"
    )
    with pytest.raises(BadRequestError, match="Missing or empty Host header."):
        Request(raw_request)


def test_invalid_headers():
    raw_request = "GET /api/resource HTTP/1.1\r\nInvalid-Header-Format\r\n\r\n"
    with pytest.raises(BadRequestError, match="Invalid headers in request."):
        Request(raw_request)


def test_no_host_header():
    raw_request = "GET /api/resource HTTP/1.1\r\n\r\n"
    with pytest.raises(BadRequestError, match="Missing or empty Host header."):
        Request(raw_request)


def test_multiple_same_headers():
    raw_request = (
        "GET /api/resource HTTP/1.1\r\n"
        "Host: localhost:8080\r\n"
        "Host: localhost:8081\r\n\r\n"
    )
    with pytest.raises(
        BadRequestError, match="Multiple headers with same key: Host."
    ):
        Request(raw_request)


def test_empty_header_key():
    raw_request = "GET /api/resource HTTP/1.1\r\n: value\r\n\r\n"
    with pytest.raises(
        BadRequestError, match="Header key or value cannot be empty."
    ):
        Request(raw_request)


def test_empty_header_value():
    raw_request = "GET /api/resource HTTP/1.1\r\nkey: \r\n\r\n"
    with pytest.raises(
        BadRequestError, match="Header key or value cannot be empty."
    ):
        Request(raw_request)


def test_invalid_query_params():
    raw_request = (
        "GET /api/resource?key=value&badquery HTTP/1.1\r\n"
        "Host: localhost:8080\r\n\r\n"
    )
    with pytest.raises(
        BadRequestError,
        match="Invalid query parameters: bad query field: 'badquery'.",
    ):
        Request(raw_request)


def test_parse_body_post_with_valid_body():
    raw_request = (
        "POST / HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Content-Length: 11\r\n"
        "\r\n"
        "Hello World"
    )
    request = Request(raw_request)
    assert request._parse_body() == "Hello World"


def test_parse_body_post_with_missing_body_separator():
    raw_request = (
        "POST / HTTP/1.1\r\n" "Host: example.com\r\n" "Content-Length: 11"
    )
    with pytest.raises(
        BadRequestError, match="Missing body separator in the request."
    ):
        Request(raw_request)


def test_parse_body_get_with_missing_body_separator():
    raw_request = (
        "GET / HTTP/1.1\r\n" "Host: example.com\r\n" "Content-Length: 11"
    )
    request = Request(raw_request)
    assert request.body is None


def test_parse_body_post_with_mismatched_content_length():
    raw_request = (
        "POST / HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Content-Length: 5\r\n"
        "\r\n"
        "Too long body"
    )
    with pytest.raises(
        BadRequestError, match="Content-Length does not match body length."
    ):
        Request(raw_request)


def test_parse_body_post_with_invalid_content_length():
    raw_request = (
        "POST / HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Content-Length: invalid\r\n"
        "\r\n"
        "Hello World"
    )
    with pytest.raises(
        BadRequestError, match="Invalid Content-Length header."
    ):
        Request(raw_request)


def test_parse_body_post_with_empty_body():
    raw_request = (
        "POST / HTTP/1.1\r\n"
        "Host: example.com\r\n"
        "Content-Length: 0\r\n"
        "\r\n"
    )
    with pytest.raises(
        BadRequestError, match="Missing body content in request."
    ):
        Request(raw_request)


def test_parse_body_get_with_no_body():
    raw_request = "GET / HTTP/1.1\r\n" "Host: example.com\r\n" "\r\n"
    request = Request(raw_request)
    assert request.body is None


def test_parse_body_post_without_content_length():
    raw_request = (
        "POST / HTTP/1.1\r\n" "Host: example.com\r\n" "\r\n" "Hello World"
    )
    request = Request(raw_request)
    assert request.body == "Hello World"


def test_parse_body_content_json_valid():
    raw_request = (
        "POST /test HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: 25\r\n\r\n"
        '{"key": "value", "id": 1}'
    )
    request = Request(raw_request)
    assert request.parsed_body == {"key": "value", "id": 1}


def test_parse_body_content_json_invalid():
    raw_request = (
        "POST /test HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: 16\r\n\r\n"
        '{"key": "value", '
    )

    with pytest.raises(
        BadRequestError,
        match="Invalid JSON in request body.",
    ):
        Request(raw_request)


def test_parse_body_content_form_data_valid():
    raw_request = (
        "POST /test HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "Content-Type: application/x-www-form-urlencoded\r\n"
        "Content-Length: 14\r\n\r\n"
        "key=value&id=1"
    )
    request = Request(raw_request)
    assert request.parsed_body == {"key": "value", "id": "1"}


def test_parse_body_content_form_data_invalid():
    raw_request = (
        "POST /test HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "Content-Type: application/x-www-form-urlencoded\r\n"
        "Content-Length: 12\r\n\r\n"
        "key=value&id"
    )
    with pytest.raises(
        BadRequestError, match="Invalid form data in request body."
    ):
        Request(raw_request)


def test_parse_body_content_plain_text():
    raw_request = (
        "POST /test HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "Content-Type: text/plain\r\n"
        "Content-Length: 11\r\n\r\n"
        "Hello World"
    )
    request = Request(raw_request)
    assert request.parsed_body == "Hello World"


def test_parse_body_content_no_content_type():
    raw_request = (
        "POST /test HTTP/1.1\r\n"
        "Host: localhost\r\n"
        "Content-Length: 11\r\n\r\n"
        "Hello World"
    )
    request = Request(raw_request)
    assert request._parse_body_content() == "Hello World"
