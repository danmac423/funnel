import pytest
from funnel.request import Request
from funnel.exceptions import BadRequestError


def test_valid_get_request():
    raw_request = (
        "GET /api/resource?key=value HTTP/1.1\r\n"
        "Host: localhost:8080\r\n"
        "User-Agent: TestClient\r\n\r\n"
    )
    request = Request(raw_request)

    assert request.method == "GET"
    assert request.path == "/api/resource?key=value"
    assert request.protocol == "HTTP/1.1"
    assert request.headers == {
        "Host": "localhost:8080",
        "User-Agent": "TestClient",
    }
    assert request.query_params == {"key": "value"}
    assert request.body == ""
    assert request.parsed_body == ""


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


def test_invalid_json_body():
    raw_request = (
        "POST /api/resource HTTP/1.1\r\n"
        "Host: localhost:8080\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: 20\r\n\r\n"
        '{"key": "value", "test": }'
    )
    with pytest.raises(BadRequestError, match="Invalid JSON in request body."):
        Request(raw_request)


def test_invalid_form_data_body():
    raw_request = (
        "POST /submit-form HTTP/1.1\r\n"
        "Host: localhost:8080\r\n"
        "Content-Type: application/x-www-form-urlencoded\r\n"
        "Content-Length: 20\r\n\r\n"
        "username=test&age"
    )
    with pytest.raises(
        BadRequestError, match="Invalid form data in request body."
    ):
        Request(raw_request)


def test_missing_body_for_post_request():
    raw_request = (
        "POST /api/resource HTTP/1.1\r\n"
        "Host: localhost:8080\r\n"
        "Content-Type: application/json\r\n"
        "Content-Length: 0\r\n\r\n"
    )
    with pytest.raises(BadRequestError, match="Missing body in POST request."):
        Request(raw_request)
