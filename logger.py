import datetime
import json


class Logger():

    """

    A class for logging messages to the console and to a file.

    """

    def __init__(self):
        with open("db.json", "r") as f:
            self.print_log_messages = json.load(
                f)["options"]["printLogMessages"]

    def _getCurrentTime(self) -> str:
        return datetime.datetime.now().isoformat()

    def log(
            self,
            _type: str,
            name: str,
            message: str,
            important: bool = False) -> str:
        """

        Logs a message to log.txt and optionally to the console.

        Args:
            _type (str): The type of message. Usually "trace", "debug", "info", "error", or "moderation".
            name (str): The name of the function that called the logger.
            message (str): The message to log.
            important (bool|None): Whether or not the message should be highlighted. Defaults to False.

        Returns:
            str: The message that was logged.

        """

        cur_time = self._getCurrentTime()
        _type = _type.upper()
        log_msg = f"{cur_time} [{_type}] [{name}] {message}"

        with open("log.txt", "a") as f:
            f.write(f"{log_msg}\n")

        if self.print_log_messages:
            if _type == "TRACE":
                _type = f"[\033[100m TRACE{' '*(11-len(_type))}\033[0m]"
            elif _type == "DEBUG":
                _type = f"[\033[46m DEBUG{' '*(11-len(_type))}\033[0m]"
            elif _type == "INFO":
                _type = f"[\033[42m INFO{' '*(11-len(_type))}\033[0m]"
            elif _type == "ERROR":
                _type = f"[\033[41m ERROR{' '*(11-len(_type))}\033[0m]"
            elif _type == "MODERATION":
                _type = f"[\033[43m MODERATION{' '*(11-len(_type))}\033[0m]"

            console_log_msg = f"{cur_time} {_type} [{name}] {message}"

            if important:
                print(f"--- {console_log_msg} ---")
            else:
                print(f"    {console_log_msg}")

        return log_msg
