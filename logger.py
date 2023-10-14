import datetime

def getCurrentTime() -> str:
    return datetime.datetime.now().isoformat()

def log(_type: str, name: str, message: str) -> None:
    with open("log.txt", "a") as f:
        f.write(f"{getCurrentTime()} [{_type.upper()}] [{name}] {message}\n")
    print(f"{getCurrentTime()} [{_type.upper()}] [{name}] {message}")