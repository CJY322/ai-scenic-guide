from datetime import datetime
from itertools import count
from threading import Lock

_counter = count(1)
_lock = Lock()


def generate_request_id() -> str:
    with _lock:
        sequence = next(_counter)
    return f"req-{datetime.now().strftime('%Y%m%d')}-{sequence:06d}"
