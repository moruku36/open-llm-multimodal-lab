from pathlib import Path

BASE_DIR = Path("/srv/files").resolve()


def read_report(filename: str) -> str:
    target = (BASE_DIR / filename).resolve()
    if not target.is_relative_to(BASE_DIR):
        raise ValueError("path escapes base directory")
    return target.read_text()
