"""Logging configuration for the HTTP server"""

import logging
from logging.handlers import RotatingFileHandler


class ClientAddressFilter(logging.Filter):
    """Filter to add client address to log messages

    Args:
        client_ip (str): Client IP address
        client_port (int): Client port number

    Attributes:
        client_ip (str): Client IP address
        client_port (int): Client port number
    """

    def __init__(self, client_ip=None, client_port=None):
        super().__init__()
        self.client_ip = client_ip
        self.client_port = client_port

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter to add client address to log messages

        Args:
            record (logging.LogRecord): Log record

        Returns:
            bool: True if the record is to be processed
        """
        if self.client_ip and self.client_port:
            record.client_info = f"Client {self.client_ip}:{self.client_port}"
        else:
            record.client_info = ""
        return True


formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(client_info)s - %(message)s"
)

rotating_file_handler = RotatingFileHandler("logs/server.log", maxBytes=5 * 1024 * 1024)

rotating_file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger = logging.getLogger("HTTP Server")
logger.setLevel(logging.INFO)
logger.addHandler(rotating_file_handler)
logger.addHandler(stream_handler)
logger.addFilter(ClientAddressFilter())
