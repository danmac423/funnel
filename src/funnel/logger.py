import logging
from logging.handlers import RotatingFileHandler


class ClientAddressFilter(logging.Filter):
    def __init__(self, client_ip=None, client_port=None):
        super().__init__()
        self.client_ip = client_ip
        self.client_port = client_port

    def filter(self, record):
        if self.client_ip and self.client_port:
            record.client_info = f"Client {self.client_ip}:{self.client_port}"
        else:
            record.client_info = ""
        return True

formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(client_info)s - %(message)s"
)

rotating_file_handler = RotatingFileHandler(
    "logs/server.log", maxBytes=5 * 1024 * 1024
)

rotating_file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger = logging.getLogger("HTTP Server")
logger.setLevel(logging.INFO)
logger.addHandler(rotating_file_handler)
logger.addHandler(stream_handler)
logger.addFilter(ClientAddressFilter())