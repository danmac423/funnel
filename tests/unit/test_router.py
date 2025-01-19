import pytest

from funnel.exceptions import MethodNotAllowedError, NotFoundError
from funnel.router import Router


def test_add_static_route():
    router = Router()

    def handler():
        return "Static Handler"

    router._add_route("/static", ["GET"], handler)

    assert router.get_handler("/static", "GET") == handler


def test_add_dynamic_route():
    router = Router()

    def handler():
        return "Dynamic Handler"

    router._add_route("/dynamic/<path:subpath>", ["GET"], handler)

    assert router.get_handler("/dynamic/some/path", "GET") == handler
    assert router.get_handler("/dynamic/another/path", "GET") == handler


def test_add_route_with_host():
    router = Router()

    def handler():
        return "Host Specific Handler"

    router._add_route("/hosted", ["GET"], handler, host="example.com")

    assert router.get_handler("/hosted", "GET", host="example.com") == handler


def test_add_duplicate_route():
    router = Router()

    def handler():
        return "Handler"

    router._add_route("/duplicate", ["GET"], handler)

    with pytest.raises(ValueError, match="Route already exists for GET /duplicate"):
        router._add_route("/duplicate", ["GET"], handler)


def test_match_static_route():
    router = Router()

    def handler():
        return "Static Handler"

    router._add_route("/static", ["GET"], handler)

    assert router.get_handler("/static", "GET") == handler


def test_match_dynamic_route():
    router = Router()

    def handler():
        return "Dynamic Handler"

    router._add_route("/dynamic/<path:subpath>", ["GET"], handler)

    assert router.get_handler("/dynamic/some/path", "GET") == handler


def test_match_route_with_host():
    router = Router()

    def handler():
        return "Host Specific Handler"

    router._add_route("/hosted", ["GET"], handler, host="example.com")

    assert router.get_handler("/hosted", "GET", host="example.com") == handler


def test_match_route_without_host():
    router = Router()

    def handler():
        return "Generic Handler"

    router._add_route("/route", ["GET"], handler)

    assert router.get_handler("/route", "GET", host="example.com") == handler
    assert router.get_handler("/route", "GET") == handler


def test_match_static_over_dynamic():
    router = Router()

    def static_handler():
        return "Static Handler"

    def dynamic_handler():
        return "Dynamic Handler"

    router._add_route("/route", ["GET"], static_handler)
    router._add_route("/<path:subpath>", ["GET"], dynamic_handler)

    assert router.get_handler("/route", "GET") == static_handler
    assert router.get_handler("/dynamic/path", "GET") == dynamic_handler


def test_not_found_static_route():
    router = Router()

    with pytest.raises(NotFoundError, match="No route found for path: /nonexistent"):
        router.get_handler("/nonexistent", "GET")


def test_not_found_dynamic_route():
    router = Router()

    def handler():
        return "Dynamic Handler"

    router._add_route("/dynamic/<path:subpath>", ["GET"], handler)

    with pytest.raises(NotFoundError, match="No route found for path: /nonexistent"):
        router.get_handler("/nonexistent", "GET")


def test_method_not_allowed_static():
    router = Router()

    def handler():
        return "Static Handler"

    router._add_route("/static", ["GET"], handler)

    with pytest.raises(
        MethodNotAllowedError,
        match="Method POST not allowed for path: /static",
    ):
        router.get_handler("/static", "POST")


def test_method_not_allowed_dynamic():
    router = Router()

    def handler():
        return "Dynamic Handler"

    router._add_route("/dynamic/<path:subpath>", ["GET"], handler)

    with pytest.raises(
        MethodNotAllowedError,
        match="Method POST not allowed for dynamic path: /dynamic/some/path",
    ):
        router.get_handler("/dynamic/some/path", "POST")


def test_method_not_allowed_for_route_without_host():
    router = Router()

    def handler():
        return "Generic Handler"

    router._add_route("/route", ["GET"], handler)

    with pytest.raises(
        MethodNotAllowedError,
        match="Method POST not allowed for path: /route without host",
    ):
        router.get_handler("/route", "POST", host="example.com")


def test_route_decorator():
    router = Router()

    @router.route("/decorated", methods=["GET"])
    def handler():
        return "Decorated Handler"

    assert router.get_handler("/decorated", "GET")() == "Decorated Handler"


def test_decorator_with_host():
    router = Router()

    @router.route("/decorated", methods=["GET"], host="example.com")
    def handler():
        return "Decorated with Host"

    assert router.get_handler("/decorated", "GET", host="example.com")() == "Decorated with Host"
    with pytest.raises(NotFoundError):
        router.get_handler("/decorated", "GET")
