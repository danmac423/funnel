import pytest

from funnel.router import Router
from funnel.exceptions import NotFoundError, MethodNotAllowedError


def test_add_route():
    router = Router()

    def handler():
        return "This is home"

    router.add_route("/home", ["GET"], handler)

    assert "/home" in router.routes
    assert "GET" in router.routes["/home"]
    assert router.routes["/home"]["GET"]() == "This is home"


def test_add_route_duplicate():
    router = Router()

    def handler():
        return "This is home"

    router.add_route("/home", ["GET"], handler)

    with pytest.raises(ValueError, match="Route already exists for GET /home"):
        router.add_route("/home", ["GET"], handler)


def test_get_handler_path_not_found():
    router = Router()

    with pytest.raises(NotFoundError, match="No route found for path: /home"):
        router.get_handler("/home", "GET")


def test_get_handler_method_not_allowed():
    router = Router()

    def handler():
        return "This is home"

    router.add_route("/home", ["POST"], handler)

    with pytest.raises(
        MethodNotAllowedError, match="Method GET not allowed for path: /home"
    ):
        router.get_handler("/home", "GET")


def test_get_handler():
    router = Router()

    def handler():
        return "This is home"

    router.add_route("/home", ["GET"], handler)

    assert router.get_handler("/home", "GET")() == "This is home"


def test_route_decorator():
    router = Router()

    @router.route("/home", ["GET"])
    def handler():
        return "This is home"

    assert "/home" in router.routes
    assert "GET" in router.routes["/home"]
    assert router.routes["/home"]["GET"]() == "This is home"
