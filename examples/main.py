from funnel.funnel import HTTPServer
from funnel.response import Response
from funnel.auth import Auth
from funnel.user_source import JsonUserSource
from datetime import datetime, timedelta, timezone
import jwt



auth = Auth()
auth.configure_user_source(JsonUserSource("users.json"))

server = HTTPServer(host="127.0.0.1", port=8000)



@server.route("/login", methods=["POST"])
def login(request):
    credentials = request.parsed_body
    username = credentials.get("username")
    password = credentials.get("password")

    user = auth.user_source.get_user(username)
    if not user or password != user["password"]:
        return Response.json(401, "Unauthorized", {
            "error": "Invalid credentials"
        })

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
def protected_endpoint(request):
    return Response.json(
        200,
        "OK",
        {"message": "Welcome!"}
    )

@server.route("/protected_basic", methods=["GET"])
@auth.authenticate(type="Basic")
def protected_endpoint(request):
    return Response.json(
        200,
        "OK",
        {"message": "Welcome!"}
    )


@server.route("/data", methods=["GET", "POST"])
def handle_data(request):
    return Response.json(
        201,
        "Created",
        {"message": "Data received", "data": request.parsed_body},
    )


if __name__ == "__main__":
    server.start()
