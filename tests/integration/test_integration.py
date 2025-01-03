import requests
import multiprocessing
import time
import os
from funnel.funnel import HTTPServer
from funnel.response import Response

TEST_PATH = "./tests/integration/"


def run_server():
    """Funkcja do uruchomienia serwera w osobnym procesie."""
    server = HTTPServer(f"{TEST_PATH}test_config.yaml")
    server.route("/hello", methods=["GET"])(
        lambda req: Response.html(
            status_code=200, reason="OK", html_content="<h1>Hello, World!</h1>"
        )
    )
    server.start()


def test_get_request():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get("http://127.0.0.1:8080/hello")
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/html"
        assert "<h1>Hello, World!</h1>" in response.text
    finally:
        process.terminate()


def test_get_file():
    process = multiprocessing.Process(target=run_server)
    process.start()

    expected_body = """
    host: "127.0.0.1"
    port: 8080
    max_workers: 10
    mounted_directories:""".replace("    ", "").strip()

    try:
        for _ in range(10):
            try:
                response = requests.get(
                    "http://127.0.0.1:8080/project/tests/integration/test_config.yaml"
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")
        assert response.status_code == 200
        assert (
            response.headers["Content-Disposition"]
            == 'attachment; filename="test_config.yaml"'
        )
        assert expected_body in response.text
    finally:
        process.terminate()


def test_get_directory():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get("http://127.0.0.1:8080/project/tests/")
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")
        expected_entries = sorted(os.listdir(f"{TEST_PATH}../"))

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/html"
        assert "<h1>Index of /project/tests</h1>" in response.text
        for entry in expected_entries:
            assert (
                f"<li><a href='/project/tests/{entry}'>{entry}</a></li>"
                in response.text
            )

    finally:
        process.terminate()
