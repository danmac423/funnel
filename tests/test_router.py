import pytest

from funnel.router import Router, RouteKey
from funnel.exceptions import NotFoundError, MethodNotAllowedError


def test_add_route():
    router = Router()

    def handler():
        return "This is home"

    router._add_route("/home", ["GET"], handler)

    route_key = RouteKey(host=None, path="/home")
    assert route_key in router.routes
    assert "GET" in router.routes[route_key]
    assert router.routes[route_key]["GET"]() == "This is home"


def test_add_route_with_host():
    router = Router()

    def handler():
        return "This is home"

    router._add_route("/home", ["GET"], handler, host="example.com")

    route_key = RouteKey(host="example.com", path="/home")
    assert route_key in router.routes
    assert "GET" in router.routes[route_key]
    assert router.routes[route_key]["GET"]() == "This is home"


def test_add_route_duplicate():
    router = Router()

    def handler():
        return "This is home"

    router._add_route("/home", ["GET"], handler)

    with pytest.raises(ValueError, match="Route already exists for GET /home"):
        router._add_route("/home", ["GET"], handler)


def test_get_handler_path_not_found():
    router = Router()

    with pytest.raises(NotFoundError, match="No route found for path: /home"):
        router.get_handler("/home", "GET")


def test_get_handler_method_not_allowed():
    router = Router()

    def handler():
        return "This is home"

    router._add_route("/home", ["POST"], handler)

    with pytest.raises(
        MethodNotAllowedError, match="Method GET not allowed for path: /home"
    ):
        router.get_handler("/home", "GET")


def test_get_handler_with_host():
    router = Router()

    def handler():
        return "This is home"

    router._add_route("/home", ["GET"], handler, host="example.com")

    assert (
        router.get_handler("/home", "GET", host="example.com")()
        == "This is home"
    )

    with pytest.raises(NotFoundError, match="No route found for path: /home"):
        router.get_handler("/home", "GET", host="another.com")


def test_get_handler_fallback_to_default_host():
    router = Router()

    def handler():
        return "Default host"

    router._add_route("/home", ["GET"], handler)

    assert (
        router.get_handler("/home", "GET", host="example.com")()
        == "Default host"
    )


def test_route_decorator():
    router = Router()

    @router.route("/home", methods=["GET"])
    def handler():
        return "This is home"

    route_key = RouteKey(host=None, path="/home")
    assert route_key in router.routes
    assert "GET" in router.routes[route_key]
    assert router.routes[route_key]["GET"]() == "This is home"


def test_route_decorator_with_host():
    router = Router()

    @router.route("/home", methods=["GET"], host="example.com")
    def handler():
        return "This is home"

    route_key = RouteKey(host="example.com", path="/home")
    assert route_key in router.routes
    assert "GET" in router.routes[route_key]
    assert router.routes[route_key]["GET"]() == "This is home"
