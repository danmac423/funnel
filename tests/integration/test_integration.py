import base64
import multiprocessing
import os
import time

import requests

from funnel.auth import Auth
from funnel.funnel import HTTPServer
from funnel.response import Response
from funnel.user_source import JsonUserSource

TEST_PATH = "./tests/integration/"

multiprocessing.set_start_method("spawn", force=True)


def configure_server() -> HTTPServer:
    """Configure server like in main."""
    auth = Auth()
    auth.configure_user_source(JsonUserSource(f"{TEST_PATH}users.json"))

    server = HTTPServer(
        f"{TEST_PATH}test_config.yaml",
    )

    @server.route("/login", methods=["POST"])
    def login(request):
        credentials = request.parsed_body
        username = credentials.get("username")
        password = credentials.get("password")

        if auth.user_source is None:
            return Response.json(
                500,
                "Internal Server Error",
                {"error": "User source not configured"},
            )

        user = auth.user_source.get_user(username)
        if not user or password != user["password"]:
            return Response.json(
                401, "Unauthorized", {"error": "Invalid credentials"}
            )

        payload = {"username": username}
        token = auth.generate_token(payload)

        return Response.json(200, "OK", {"token": token})

    @server.route("/", methods=["GET"])
    def home(request):
        return Response.html(200, "OK", "<h1>Welcome to the Home Page!</h1>")

    @server.route("/", methods=["GET"], host="example.com")
    def home_example(request):
        return Response.html(
            200, "OK", "<h1>Welcome to the Home Page of example.com host!</h1>"
        )

    @server.route("/about", methods=["GET"])
    def about(request):
        return Response.html(200, "OK", "<h1>About this Server</h1>")

    @server.route("/protected_bearer", methods=["GET"])
    @auth.authenticate(type="Bearer")
    def protected_endpoint_bearer(request):
        return Response.json(200, "OK", {"message": "Welcome!"})

    @server.route("/protected_basic", methods=["GET"])
    @auth.authenticate(type="Basic")
    def protected_endpoint_basic(request):
        return Response.json(200, "OK", {"message": "Welcome!"})

    @server.route("/data", methods=["GET", "POST"])
    def handle_data(request):
        return Response.json(
            201,
            "Created",
            {"message": "Data received", "data": request.parsed_body},
        )

    @server.route("/internal_error", methods=["GET"])
    def error(request):
        raise Exception("Internal error")

    @server.route("/hello", methods=["GET"])
    def hello(request):
        return Response.html(200, "OK", "<h1>Hello, World!</h1>")

    return server


def run_server():
    """Funkcja do uruchomienia serwera w osobnym procesie."""
    server = configure_server()
    server.start()


def test_get_request():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get("http://127.0.0.1:8080/")
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


def test_home_example():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                response = requests.get(
                    "http://127.0.0.1:8080/", headers={"Host": "example.com"}
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 200
        assert response.headers["Content-Type"] == "text/html"
        assert (
            "<h1>Welcome to the Home Page of example.com host!</h1>"
            in response.text
        )
    finally:
        process.terminate()


def test_handle_data_post():
    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                payload = {"key": "value"}
                response = requests.post(
                    "http://127.0.0.1:8080/data",
                    json=payload,
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 201
        assert response.headers["Content-Type"] == "application/json"
        assert "message" in response.json()
        assert response.json()["message"] == "Data received"
        assert response.json()["data"] == {"key": "value"}
    finally:
        process.terminate()


def test_login():
    os.environ["SECRET_KEY"] = "mocked_secret_key"

    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                payload = {"username": "john_doe", "password": "admin123"}
                response = requests.post(
                    "http://127.0.0.1:8080/login",
                    json=payload,
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 200
        assert response.json()["token"] is not None
    finally:
        process.terminate()


def test_authorization_bearer():
    os.environ["SECRET_KEY"] = "mocked_secret_key"

    process = multiprocessing.Process(target=run_server)
    process.start()

    try:
        for _ in range(10):
            try:
                payload = {"username": "john_doe", "password": "admin123"}
                response = requests.post(
                    "http://127.0.0.1:8080/login",
                    json=payload,
                )
                token = response.json()["token"]
                response = requests.get(
                    "http://127.0.0.1:8080/protected_bearer",
                    headers={"Authorization": f"Bearer {token}"},
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 200
    finally:
        process.terminate()


def test_authorization_basic():
    process = multiprocessing.Process(target=run_server)
    process.start()

    login = "john_doe"
    password = "admin123"
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

        assert response.status_code == 200
    finally:
        process.terminate()


def test_range_header_support():
    process = multiprocessing.Process(target=run_server)
    process.start()

    file_path = os.path.join("tests/integration/", "test_file.txt")
    with open(file_path, "w") as f:
        f.write("This is a test file for Range header support.")

    try:
        for _ in range(10):
            try:
                response = requests.get(
                   "http://127.0.0.1:8080/project/tests/integration/test_file.txt",
                    headers={"Range": "bytes=0-4"},
                )
                break
            except requests.ConnectionError:
                time.sleep(0.5)
        else:
            raise RuntimeError("Server did not start in time.")

        assert response.status_code == 206
        assert response.headers["Content-Range"] == "bytes 0-4/45"
        assert response.text == "This "

    finally:
        process.terminate()
        if os.path.exists(file_path):
            os.remove(file_path)

