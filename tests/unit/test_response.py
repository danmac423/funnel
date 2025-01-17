import json

from funnel.response import Response


def test_response_default():
    response = Response()
    http_response = response.to_http().decode("utf-8")

    assert http_response.startswith("HTTP/1.1 200 OK")
    assert "Content-Length: 0" in http_response
    assert http_response.endswith("\r\n\r\n")


def test_response_with_body():
    response = Response(body="Hello, World!")
    http_response = response.to_http().decode("utf-8")

    assert http_response.startswith("HTTP/1.1 200 OK")
    assert "Content-Length: 13" in http_response
    assert http_response.endswith("Hello, World!")


def test_response_with_headers():
    response = Response(headers={"Test-Header": "Test Value"})
    http_response = response.to_http().decode("utf-8")

    assert http_response.startswith("HTTP/1.1 200 OK")
    assert "Test-Header: Test Value" in http_response


def test_set_header():
    response = Response()
    response.set_header("Test-Header", "Test Value")

    http_response = response.to_http().decode("utf-8")

    assert http_response.startswith("HTTP/1.1 200 OK")
    assert "Test-Header: Test Value" in http_response


def test_json_response():
    data = {"key": "value"}
    response = Response.json(200, "OK", data)
    http_response = response.to_http().decode("utf-8")

    assert http_response.startswith("HTTP/1.1 200 OK")
    assert "Content-Type: application/json" in http_response
    assert "Content-Length: 16" in http_response
    assert json.loads(http_response.split("\r\n\r\n")[1]) == data


def test_json_response_with_headers():
    data = {"key": "value"}
    response = Response.json(
        200, "OK", json_data=data, headers={"Test-Header": "Test Value"}
    )
    http_response = response.to_http().decode("utf-8")

    assert http_response.startswith("HTTP/1.1 200 OK")
    assert "Test-Header: Test Value" in http_response
    assert "Content-Type: application/json" in http_response
    assert "Content-Length: 16" in http_response
    assert json.loads(http_response.split("\r\n\r\n")[1]) == data


def test_html_response():
    html_content = "<h1>Hello, World!</h1>"
    response = Response.html(200, "OK", html_content)
    http_response = response.to_http().decode("utf-8")

    assert http_response.startswith("HTTP/1.1 200 OK")
    assert "Content-Type: text/html" in http_response
    assert "Content-Length: 22" in http_response
    assert http_response.endswith(html_content)


def test_response_with_binary_body():
    binary_data = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    response = Response(
        status_code=200,
        reason="OK",
        headers={"Content-Type": "image/png"},
        body=binary_data,
    )
    http_response = response.to_http()

    assert http_response.startswith(b"HTTP/1.1 200 OK")
    assert b"Content-Type: image/png" in http_response
    assert b"Content-Length: 16" in http_response
    assert http_response.endswith(binary_data)


def test_response_with_empty_body():
    response = Response()
    http_response = response.to_http()

    assert http_response.startswith(b"HTTP/1.1 200 OK")
    assert b"Content-Length: 0" in http_response
    assert http_response.endswith(b"\r\n\r\n")


def test_response_with_custom_status():
    response = Response(status_code=404, reason="Not Found")
    http_response = response.to_http().decode("utf-8")

    assert http_response.startswith("HTTP/1.1 404 Not Found")
    assert "Content-Length: 0" in http_response


def test_response_with_combined_headers_and_body():
    response = Response(
        status_code=200,
        reason="OK",
        headers={"Custom-Header": "CustomValue"},
        body="Custom Body",
    )
    http_response = response.to_http().decode("utf-8")

    assert http_response.startswith("HTTP/1.1 200 OK")
    assert "Custom-Header: CustomValue" in http_response
    assert "Content-Length: 11" in http_response
    assert http_response.endswith("Custom Body")
