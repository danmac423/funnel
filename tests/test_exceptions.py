import funnel.exceptions as ex


def test_error_to_json():
    error = ex.FunnelError()

    assert error.to_json() == {
        "error": "An internal server error occurred.",
        "status_code": 500,
    }
