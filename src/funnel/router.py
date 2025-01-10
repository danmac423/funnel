"""
This module contains the Router class to manage routes and handlers.
"""

import os
import re
from dataclasses import dataclass
from typing import Callable, Optional

from funnel.exceptions import MethodNotAllowedError, NotFoundError


@dataclass(frozen=True)
class RouteKey:
    """
    Dataclass to represent a route key.

    Attributes:
        host (Optional[str]): Host of the route
        path (str): Path of the route
    """

    host: Optional[str]  # None if no host is specified
    path: str


class Router:
    """
    Router class to manage routes and handlers.

    Attributes:
        self.static_routes (dict[RouteKey, dict[str, Callable]]): Dictionary of
            static routes
        self.dynamic_routes (list[tuple[
                                RouteKey,
                                re.Pattern,
                                dict[str, Callable
                                ]]]): List of dynamic routes
    """

    def __init__(self):
        self.static_routes: dict[RouteKey, dict[str, Callable]] = {}
        self.dynamic_routes: list[
            tuple[RouteKey, re.Pattern, dict[str, Callable]]
        ] = []

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
            host (Optional[str]): Host of the route
        """
        normalized_path = os.path.normpath(path)
        route_key = RouteKey(host=host, path=normalized_path)

        if "<" in path and ">" in path:
            regex_path = re.sub(r"<\w+:[^>]+>", r".*", normalized_path)
            regex = re.compile(f"^{regex_path}$")
            self.dynamic_routes.append(
                (route_key, regex, {method: handler for method in methods})
            )
        else:
            if route_key not in self.static_routes:
                self.static_routes[route_key] = {}
            for method in methods:
                if method in self.static_routes[route_key]:
                    raise ValueError(
                        f"Route already exists for {method} {normalized_path}"
                    )
                self.static_routes[route_key][method] = handler

    def get_handler(
        self, path: str, method: str, host: Optional[str] = None
    ) -> Callable:
        """
        Get the handler for a path and method.

        Args:
            path (str): Path of the route
            method (str): Method of the route
            host (Optional[str]): Host of the route

        Returns:
            Callable: Handler function
        """
        normalized_path = os.path.normpath(path)

        route_key = RouteKey(host=host, path=normalized_path)
        if route_key in self.static_routes:
            if method in self.static_routes[route_key]:
                return self.static_routes[route_key][method]
            raise MethodNotAllowedError(
                f"Method {method} not allowed for path: {path}"
            )

        route_key = RouteKey(host=None, path=normalized_path)
        if route_key in self.static_routes:
            if method in self.static_routes[route_key]:
                return self.static_routes[route_key][method]
            raise MethodNotAllowedError(
                f"Method {method} not allowed for path: {path} without host"
            )

        for route_key, regex, methods in self.dynamic_routes:
            if route_key.host == host or route_key.host is None:
                if regex.fullmatch(normalized_path):
                    if method in methods:
                        return methods[method]
                    raise MethodNotAllowedError(
                        f"Method {method} not allowed for dynamic path: {path}"
                    )

        raise NotFoundError(f"No route found for path: {path}")

    def route(
        self, path: str, *, methods: list[str], host: Optional[str] = None
    ) -> Callable:
        """
        Decorator to add a route.

        Args:
            path (str): Path of the route
            methods (list[str]): List of allowed methods
            host (Optional[str]): Host of the route

        Returns:
            Callable: Decorator function
        """

        def decorator(handler: Callable):
            self._add_route(path, methods, handler, host)

        return decorator
