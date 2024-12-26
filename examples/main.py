from funnel.funnel import HTTPServer
from funnel.response import Response
from funnel.auth import Auth
from datetime import datetime, timedelta, timezone
from funnel.logging_helper import get_user_from_file
from funnel.exceptions import UnauthorizedError
import jwt

auth = Auth()
server = HTTPServer(host="127.0.0.1", port=8001)

SECRET_KEY = "abc123"


def generate_test_token():
    now = datetime.now(timezone.utc)
    payload = {
        "username": "john_doe",
        "password": "admin123",
        "exp": now + timedelta(hours=1),
        "iat": now,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


@server.route("/login", methods=["POST"])
def login(request):
    credentials = request.parsed_body
    username = credentials.get("username")
    password = credentials.get("password")

    user = get_user_from_file(username, "users.json")
    if not user or password != user["password"]:
        return Response.json(401, "Unauthorized", {"error": "Invalid credentials"})

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


@server.route("/protected", methods=["GET"])
@auth.authenticate(user_file="users.json", type="Bearer")
def protected_endpoint(request):
    return Response.json(
        200,
        "OK",
        {"message": f"Welcome, {request.user['username']}!"},
    )


@server.route("/data", methods=["GET", "POST"])
def handle_data(request):
    return Response.json(
        201,
        "Created",
        {"message": "Data received", "data": request.parsed_body},
    )


if __name__ == "__main__":
    # print(generate_test_token())
    server.start()
