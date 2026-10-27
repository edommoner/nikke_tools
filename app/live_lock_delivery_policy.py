"""Explicit partial lowering: live frozen recipients; unresolved death fails closed."""
from lock_delivery_policy import select,MODEL as SNAPSHOT_MODEL

MODEL='require-live-frozen-slot-v1'

class UnresolvedLockDelivery(ValueError):
    pass

def select_live(snapshot,hit,hits,views,*,model):
    if model!=MODEL:raise ValueError('Explicit live lock delivery model required')
    result=select(snapshot,hit,hits,views,model=SNAPSHOT_MODEL)
    if result.status not in (0,1):
        raise UnresolvedLockDelivery('Unresolved dead/missing/stale lock delivery: '+str(result.status))
    return result
