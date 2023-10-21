import datetime
import json

class Logger():

    """

    A class for logging messages to the console and to a file.

    """

    def __init__(self):
        with open("db.json", "r") as f:
            self.print_log_messages = json.load(f)["options"]["printLogMessages"]

    def _getCurrentTime(self) -> str:
        return datetime.datetime.now().isoformat()

    def log(self, _type: str, name: str, message: str, important: bool = False) -> str:

        """
        
        Logs a message to the console and to a file.

        Args:
            _type (str): The type of message. Usually "info", "debug", "error", or "moderation".
            name (str): The name of the function that called the logger.
            message (str): The message to log.
            important (bool|None): Whether or not the message should be highlighted. Defaults to False.

        Returns:
            str: The message that was logged.
        
        """

        if important:
            log_msg = f"| {self._getCurrentTime()} [{_type.upper()}] [{name}] {message}"
        else:
            log_msg = f"{self._getCurrentTime()} [{_type.upper()}] [{name}] {message}"

        with open("log.txt", "a") as f:
            f.write(f"{log_msg}\n")

        if self.print_log_messages:
            print(f"{log_msg}")
            
        return log_msg