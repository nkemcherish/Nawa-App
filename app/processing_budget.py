"""Per-request processing deadline; no document content is recorded."""
from contextlib import contextmanager
from contextvars import ContextVar
import time

_deadline=ContextVar('nawa_processing_deadline',default=None)


class ProcessingTimeout(ValueError):
    pass


@contextmanager
def processing_budget(seconds=240):
    token=_deadline.set(time.monotonic()+seconds)
    try: yield
    finally: _deadline.reset(token)


def check_budget(reserve=5):
    deadline=_deadline.get()
    remaining=None if deadline is None else deadline-time.monotonic()
    if remaining is not None and remaining<=reserve:
        raise ProcessingTimeout('This statement took longer than the reader can process in one request. '
                                'No partial report was saved. Try a shorter date range or a CSV export.')
    return remaining


def io_timeout(default):
    remaining=check_budget()
    return default if remaining is None else min(default,max(1,remaining-5))
