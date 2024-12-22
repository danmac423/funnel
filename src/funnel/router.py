"""
This module contains the Router class to manage routes and handlers.
"""

from typing import Callable

from funnel.exceptions import MethodNotAllowedError, NotFoundError


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
        self.routes: dict[str, dict[str, Callable]] = {}

    def add_route(
        self, path: str, methods: list[str], handler: Callable
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
        if path not in self.routes:
            self.routes[path] = {}

        for method in methods:
            if method in self.routes[path]:
                raise ValueError(f"Route already exists for {method} {path}")
            self.routes[path][method] = handler

    def route(self, path: str, methods: list[str]) -> Callable:
        """
        Decorator to add a route.

        Args:
            path (str): Path of the route
            methods (list[str]): List of allowed methods

        Returns:
            Callable: Decorator function
        """

        def decorator(handler: Callable):
            self.add_route(path, methods, handler)

        return decorator

    def get_handler(self, path: str, method: str) -> Callable:
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
        if path not in self.routes:
            raise NotFoundError(f"No route found for path: {path}")
        if method not in self.routes[path]:
            raise MethodNotAllowedError(
                f"Method {method} not allowed for path: {path}"
            )
        return self.routes[path][method]
