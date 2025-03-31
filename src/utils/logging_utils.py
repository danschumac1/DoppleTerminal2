import os
import threading
from datetime import datetime

class StandAloneLogger:
    """
    A standalone logger that can be instantiated multiple times for independent logging.
    """
    def __init__(self, log_path: str = "./logs/logger.log", init: bool = False, clear: bool = False):
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        if clear:
            self._clear_log()

        if init:
            self._write_header()

    def _write_header(self):
        """Writes a header indicating a new run."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = "\n" + "=" * 40 + f"\nNew Log Session at {timestamp}\n" + "=" * 40 + "\n"
        self._write_to_log(header)

    def _clear_log(self):
        """Clears the content of the log file."""
        try:
            with open(self.log_path, "w") as f:
                f.write("")
        except IOError as e:
            print(f"Error clearing log file: {e}")

    def _write_to_log(self, log_entry: str):
        """Writes a log entry to the log file."""
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
                f.flush()
        except IOError as e:
            print(f"Logging Error: {e}")

    def log(self, message: str, level: str = "INFO"):
        """Formats and writes the log message to the log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{level}] {message} || {timestamp}\n"
        self._write_to_log(log_entry)

    def info(self, message: str):
        self.log(message, "INFO")

    def warning(self, message: str):
        self.log(message, "WARNING")

    def error(self, message: str):
        self.log(message, "ERROR")

class MasterLogger:
    """
    A singleton logger that serves as the main logging system for the entire game.
    """
    _instance = None  
    _lock = threading.Lock()  

    def __new__(cls, log_path: str = "./logs/master.log", init: bool = False, clear: bool = False):
        """
        Ensures only one instance of MasterLogger is created.
        """
        with cls._lock:  
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialize(log_path, init, clear)
        return cls._instance

    def _initialize(self, log_path: str, init: bool, clear: bool):
        """
        Initializes the MasterLogger with a specific log file path.
        """
        self.log_path = log_path
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        if clear:
            self._clear_log()

        if init:
            self._write_header()

    def _write_header(self):
        """Writes a header indicating a new run."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        header = "\n" + "=" * 40 + f"\nMaster Log Session at {timestamp}\n" + "=" * 40 + "\n"
        self._write_to_log(header)

    def _clear_log(self):
        """Clears the content of the log file."""
        try:
            with open(self.log_path, "w") as f:
                f.write("")
        except IOError as e:
            print(f"Error clearing log file: {e}")

    def _write_to_log(self, log_entry: str):
        """Writes a log entry to the log file."""
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)
                f.flush()
        except IOError as e:
            print(f"Logging Error: {e}")

    def log(self, message: str, level: str = "INFO"):
        """Formats and writes the log message to the log file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{level}] {message} || {timestamp}\n"
        self._write_to_log(log_entry)

    def info(self, message: str):
        self.log(message, "INFO")

    def warning(self, message: str):
        self.log(message, "WARNING")

    def error(self, message: str):
        self.log(message, "ERROR")

    @staticmethod
    def get_instance():
        """Retrieves the singleton instance."""
        return MasterLogger._instance
