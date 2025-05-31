# **Funnel: A Lightweight, Flask-Inspired HTTP Server in Python**

[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/release/python-3130/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Welcome to **Funnel**, a custom-built HTTP server implemented from the ground up in Python. Inspired by the simplicity and elegance of frameworks like Flask, Funnel provides a robust foundation for building web services with minimal dependencies. It features a clean, decorator-based syntax for routing and authentication, making it incredibly intuitive to define endpoints and secure your application.

This project was developed as an academic endeavor to explore the inner workings of HTTP, network communication, and server architecture.

---

## **🌟 Key Features**

Funnel is packed with features that provide a comprehensive and secure server experience:

-   **Declarative Routing:** Define routes effortlessly using a `@server.route()` decorator, similar to Flask.
-   **Flexible Authentication:** Secure your endpoints with built-in **Basic** and **Bearer** authentication using a simple `@auth.authenticate()` decorator.
-   **Configuration Driven:** All server settings, including host, port, and directory mappings, are managed through a clean `YAML` configuration file.
-   **Full HTTP Method Support:** Handles `GET`, `POST`, and `DELETE` requests out-of-the-box.
-   **Static File Serving:** Mount local directories to specific URL paths to serve static assets like images, CSS, and JavaScript.
-   **Directory Indexing:** Automatically generates an HTML index view for directories, allowing users to browse file listings in their browser.
-   **Robust Error Handling:** Returns standard HTTP status codes for all common scenarios (e.g., `404 Not Found`, `401 Unauthorized`, `500 Internal Server Error`).
-   **Request Logging:** Keeps a detailed log of all incoming requests, including the client IP, HTTP method, URL path, status code, and response time.
-   **Multithreaded Architecture:** Utilizes Python's `threading` module to handle up to 10 concurrent connections, ensuring responsiveness under load.
-   **(Optional) Range Requests:** Supports the `Range` header for partial content delivery, ideal for streaming large files.

---

## **🚀 Getting Started**

### **Prerequisites**

-   Python 3.13 or newer
-   `uv` package manager

### **Installation**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/danmac423/funnel.git
    cd funnel
    ```

2.  **Set up the virtual environment and install dependencies:**
    ```bash
    make uv
    source .venv/bin/activate
    ```

3.  **Run the example server:**
    ```bash
    make run_server
    ```
    The server will start on `127.0.0.1:8080` by default.

---

## **💡 Usage**

Funnel makes it incredibly simple to create and manage your server.

### **Defining Routes**

Use the `@server.route()` decorator to map URL paths to your handler functions. You can specify which HTTP methods are allowed and even bind routes to a specific hostname.

```python
# Initialize the server with a config file
server = HTTPServer("./config/server_config.yaml")

# Define a simple GET route for a specific host
@server.route("/", methods=["GET", "POST"], host="example.com")
def home_example(request):
    return Response.html(
        200, "OK", "<h1>Welcome to the Home Page of example.com!</h1>"
    )
```

### Securing Endpoints
Protect your routes using the `@auth.authenticate()` decorator. Funnel supports both `Basic` and `Bearer` authentication schemes.

```python
# Initialize the authentication handler
auth = Auth()
auth.configure_user_source(JsonUserSource("users.json")) # Load users from a JSON file

# Secure an endpoint with Bearer token authentication
@server.route("/protected_bearer", methods=["GET"])
@auth.authenticate(type="Bearer")
def protected_endpoint_bearer(request):
    return Response.json(200, "OK", {"message": "Welcome, authenticated user!"})
``` 

## 🛠️ **Configuration**
The server is configured using a `server_config.yaml` file. This allows you to define the host, port, worker thread limit, and directories you want to serve.

**Example** `server_config.yaml`:
```yaml
host: "127.0.0.1"
port: 8080
max_workers: 10
mounted_directories:
  - path: "/static"
    directory: "./public" # Maps the /static URL to the local ./public folder
  - path: "/files"
    directory: "/var/data"
```

## 🏗️ **Architecture**
Funnel is built with a modular and maintainable architecture, consisting of two main parts:

1. HTTP Server Library (`funnel/`): The core of the project. It provides all the building blocks for creating an HTTP server.
    - `HTTPServer`: The main server class that manages sockets, handles incoming connections, and orchestrates request processing.
    - `Router`: Maps incoming requests to the correct handler functions based on path, method, and host.
    - `Request` & `Response`: Classes that represent incoming HTTP requests and outgoing responses, handling parsing and serialization.
    - `Auth`: Manages `Basic` and `Bearer` authentication logic.
    - `utils`: A module with helper functions for file operations, configuration loading, and directory serving.
2. Example Server Application (`examples/main.py`): A sample implementation that demonstrates how to use the Funnel library to build and run a functional server.

## 🧪 **Testing**
The project is thoroughly tested to ensure reliability and correctness.
- **Unit Tests**: Written with `pytest` to validate individual components like routing, authentication, and request/response handling. The project achieves **100% line coverage**.
- **Integration Tests**: Use `pytest` and the `requests` library to test the full request-response cycle and ensure all components work together seamlessly.
- **Manual Testing**: Performed using tools like `curl` and Postman to verify server behavior from a user's perspective.

## 💻 **Tech Stack & Tools**
- **Language**: Python 3.13
- **Core Libraries**: `socket`, `threading`, `os`, `pathlib`, `logging`, `json`
- **Testing**: `pytest`, `requests`
- **Development Tools**: VS Code, Git, GitHub, curl

## 👥 **The Team**
This project was a collaborative effort by:

- Daniel Machniak: Network Communication, Routing, Multithreading, and Directory Mounting.
- Krzysztof Gólcz: YAML Configuration, DELETE Method, and Directory Mounting.
- Natalia Pieczko: Authentication (Basic & Bearer), POST Method, Logging, and Range Header support.