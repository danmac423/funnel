"""
This module contains the Router class to manage routes and handlers.
"""

from typing import Callable, Optional
from dataclasses import dataclass

from funnel.exceptions import MethodNotAllowedError, NotFoundError


@dataclass(frozen=True)
class RouteKey:
    host: Optional[str]  # None if no host is specified
    path: str


class Router:
    """
    Router class to manage routes and handlers.

    Attributes:
        routes (dict[str, dict[str, Callable]]): Dictionary of routes

    Methods:
        add_route: Add a route to the router
        route: Decorator to add a route
        get_handler: Get the handler for a path and method
    """

    def __init__(self):
        self.routes: dict[RouteKey, dict[str, Callable]] = {}

    def _add_route(
        self,
        path: str,
        methods: list[str],
        handler: Callable,
        host: Optional[str] = None,
    ) -> None:
        """
        Add a route to the router.

        Args:
            path (str): Path of the route
            methods (list[str]): List of allowed methods
            handler (Callable): Handler function

        Raises:
            ValueError: If route already exists for the method and path
        """

        route_key = RouteKey(host=host, path=path)

        if route_key not in self.routes:
            self.routes[route_key] = {}

        for method in methods:
            if method in self.routes[route_key]:
                raise ValueError(f"Route already exists for {method} {path}")
            self.routes[route_key][method] = handler

    def route(
        self, path: str, *, methods: list[str], host: Optional[str] = None
    ) -> Callable:
        """
        Decorator to add a route.

        Args:
            path (str): Path of the route
            methods (list[str]): List of allowed methods

        Returns:
            Callable: Decorator function
        """

        def decorator(handler: Callable):
            self._add_route(path, methods, handler, host)

        return decorator

    def get_handler(
        self, path: str, method: str, host: Optional[str] = None
    ) -> Callable:
        """
        Get the handler for a path and method.

        Args:
            path (str): Path of the route
            method (str): Method of the route

        Raises:
            NotFoundError: If no route found for the path
            MethodNotAllowedError: If method not allowed for the path

        Returns:
            Callable: Handler function
        """

        route_key = RouteKey(host=host, path=path)

        if route_key not in self.routes:
            route_key = RouteKey(host=None, path=path)
            if route_key not in self.routes:
                raise NotFoundError(f"No route found for path: {path}")

        if method not in self.routes[route_key]:
            raise MethodNotAllowedError(
                f"Method {method} not allowed for path: {path}"
            )

        return self.routes[route_key][method]
