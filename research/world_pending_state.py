"""Read the existing pending controller counters;no reconstructed state."""
from portable_specs import LIMITS as L

def pending_state(block):
    at=L['PENDING_STATE_BASE']
    return dict(zip(('count','enqueued','fired'),block[at:at+3]))
