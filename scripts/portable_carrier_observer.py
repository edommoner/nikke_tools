"""Scoped native construction observation; never supplies GPU state or inputs."""
from contextlib import contextmanager
_observed=None

@contextmanager
def capture():
    global _observed
    from calculator.buff_manager import ActiveBuff
    assert _observed is None,'Native observation scopes must be sequential'
    original=ActiveBuff.__init__;_observed=[]
    def construct(carrier,*args,**kwargs):
        original(carrier,*args,**kwargs);_observed.append(carrier)
    ActiveBuff.__init__=construct
    try:yield
    finally:ActiveBuff.__init__=original;_observed=None

def records(manager,raw):
    assert _observed is not None,'Use capture() around the independent native observer'
    identities={id(effect):i for i,(effect,_) in enumerate(raw)}
    selected=[carrier for carrier in _observed if id(carrier.effect) in identities]
    return [dict(order=i+1,definition=identities[id(carrier.effect)],activated=carrier.activated_at) for i,carrier in enumerate(selected)]
