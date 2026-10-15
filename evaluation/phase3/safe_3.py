import json
import os
import subprocess


def load_settings(raw: bytes) -> dict:
    return json.loads(raw)


def ping(host: str) -> bytes:
    if not host.replace(".", "").replace("-", "").isalnum():
        raise ValueError("invalid host")
    return subprocess.run(["ping", "-c", "1", host], capture_output=True).stdout


API_KEY = os.environ["APP_API_KEY"]
