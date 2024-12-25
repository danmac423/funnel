from funnel.funnel import HTTPServer
from funnel.response import Response


server = HTTPServer("./config/server_config.yaml")


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


@server.route("/data", methods=["POST"])
def handle_data(request):
    return Response.json(
        201,
        "Created",
        {"message": "Data received", "data": request.parsed_body},
    )


if __name__ == "__main__":
    server.start()
