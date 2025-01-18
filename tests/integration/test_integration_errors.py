import base64
import multiprocessing
import os
import time

import requests
from test_integration import run_server

TEST_PATH = "./tests/integration/"


def test_get_missing_directory():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get(
                    "http://127.0.0.1:8080/project/tests/missing/"
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 404

    finally:
        process.terminate()


def test_get_missing_file():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get(
                    "http://127.0.0.1:8080/project/tests/missing.jpg"
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 404

    finally:
        process.terminate()


def test_invalid_host():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get(
                    "http://127.0.0.1:8080/", headers={"host": "invalid.coms"}
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 400
    finally:
        process.terminate()


def test_authorization_bearer_invalid_token():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get(
                    "http://127.0.0.1:8080/protected_bearer",
                    headers={"Authorization": "Bearer token"},
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 401
    finally:
        process.terminate()


def test_authorization_bearer_no_token():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get(
                    "http://127.0.0.1:8080/protected_bearer",
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 400
    finally:
        process.terminate()


def test_authorization_basic_wrong_creds():
    process = multiprocessing.Process(target=run_server)
    process.start()

    login = "wronglogin"
    password = "wrongpass"
    try:
        for _ in range(10):
            try:
                credentials = f"{login}:{password}"
                encoded_credentials = base64.b64encode(
                    credentials.encode()
                ).decode()
                header = {"Authorization": f"Basic {encoded_credentials}"}
                response = requests.get(
                    "http://127.0.0.1:8080/protected_basic",
                    headers=header,
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 401
    finally:
        process.terminate()


def test_authorization_basic_no_creds():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get(
                    "http://127.0.0.1:8080/protected_basic",
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 400
    finally:
        process.terminate()


def test_back_to_home_page():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get("http://127.0.0.1:8080/project/../")
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/html"
        assert "<h1>Welcome to the Home Page!</h1>" in response.text

    finally:
        process.terminate()


def test_method_not_allowed_request():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.patch("http://127.0.0.1:8080/hello")
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")
        assert response.status_code == 405
    finally:
        process.terminate()


def test_handle_data_post_invalid_json():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                payload = '{"key" "value"}'
                response = requests.post(
                    "http://127.0.0.1:8080/data",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 400
    finally:
        process.terminate()


def test_internal_error():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get(
                    "http://127.0.0.1:8080/internal_error",
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 500
    finally:
        process.terminate()


def test_post_invalid_json():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                payload = '{"key": "value", "data": true,'  # Malformed JSON
                response = requests.post(
                    "http://127.0.0.1:8080/data",
                    data=payload,
                    headers={"Content-Type": "application/json"},
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 400
        response_json = response.json()
        assert "error" in response_json
        assert "Invalid JSON" in response_json["error"]
    finally:
        process.terminate()


def test_post_large_json():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        large_payload = {"key": "value" * 10000}  # Large JSON payload
        for _ in range(10):
            try:
                response = requests.post(
                    "http://127.0.0.1:8080/data",
                    json=large_payload,
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 201
        response_json = response.json()
        assert response_json["message"] == "Data received"
    finally:
        process.terminate()


def test_post_empty_body():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.post(
                    "http://127.0.0.1:8080/data",
                    data="",  # No body
                    headers={"Content-Type": "application/json"},
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 400
        response_json = response.json()
        assert "error" in response_json
        assert "Missing body content in request" in response_json["error"]
    finally:
        process.terminate()


def test_invalid_range_format():
    process = multiprocessing.Process(target=run_server)
    process.start()

    file_path = os.path.join("tests/integration/", "test_file.txt")
    with open(file_path, "w") as f:
        f.write("This is a test file for Range header support.")

    try:
        for _ in range(10):
            try:
                # Invalid Range format
                response = requests.get(
                    "http://127.0.0.1:8080/project/tests/integration/test_file.txt",
                    headers={"Range": "bytes=abc-def"},
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        # Check response
        assert response.status_code == 400
        assert "Invalid Range header format" in response.json()["error"]

    finally:
        process.terminate()
        os.remove(file_path)


def test_out_of_bounds_range():
    process = multiprocessing.Process(target=run_server)
    process.start()

    file_path = os.path.join("tests/integration/", "test_file.txt")
    with open(file_path, "w") as f:
        f.write("This is a test file for Range header support.")


    try:
        for _ in range(10):
            try:
                # Out-of-bounds range
                response = requests.get(
                    "http://127.0.0.1:8080/project/tests/integration/test_file.txt",
                    headers={"Range": "bytes=100-200"},
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        # Check response
        assert response.status_code == 400
        assert "Invalid byte range." in response.json()["error"]

    finally:
        process.terminate()
        os.remove(file_path)


def test_invalid_range():
    process = multiprocessing.Process(target=run_server)
    process.start()

    file_path = os.path.join("tests/integration/", "test_file.txt")
    with open(file_path, "w") as f:
        f.write("This is a test file for Range header support.")


    try:
        for _ in range(10):
            try:
                # Range request on an empty file
                response = requests.get(
                    "http://127.0.0.1:8080/project/tests/integration/test_file.txt",
                    headers={"Range": "bytes=10-5"},
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        # Check response
        assert response.status_code == 400
        assert "Invalid byte range." in response.json()["error"]

    finally:
        process.terminate()
        os.remove(file_path)
