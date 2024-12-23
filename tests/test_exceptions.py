import json

import funnel.exceptions as ex


def test_default_error():
    error = ex.FunnelError()
    assert error.status_code == 500
    assert error.error_reason == "Internal Server Error"
    assert error.error_message == "An internal server error occurred."
    assert error.additional_data == {}


def test_custom_error():
    error = ex.FunnelError("Custom error", {"key": "value"})
    assert error.error_message == "Custom error"
    assert error.additional_data == {"key": "value"}


def test_error_to_dict():
    error = ex.FunnelError("Custom error", {"key": "value"})
    assert error.to_dict() == {
        "error": "Custom error",
        "status_code": 500,
        "key": "value",
    }


def test_error_to_http_response():
    error = ex.FunnelError("Custom error", {"key": "value"})
    response = error.to_http_response()
    assert response.status_code == 500
    assert response.reason == "Internal Server Error"
    assert json.loads(response.body if response.body else "") == {
        "error": "Custom error",
        "status_code": 500,
        "key": "value",
    }
