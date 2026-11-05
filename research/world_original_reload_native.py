"""Original identity observations reuse the common reload lifecycle observer."""
from contextlib import contextmanager
from world_reload_native import capture as shared_capture

@contextmanager
def capture(case):
    with shared_capture(case,original=True) as observed:yield observed
