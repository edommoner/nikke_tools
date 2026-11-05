"""Opt-in filter for the project's Python-call/return-only observation contract.

The reference calculation and Python observer order are unchanged. No profiler
sampling, battle event, numeric query or comparison is removed.
"""
import hashlib,sys,types
from pathlib import Path
from contextlib import contextmanager
RECEIPTS=[]
C_EVENTS=frozenset(('c_call','c_return','c_exception','c_'))

def observer_chain(callback):
    root=Path(__file__).resolve().parents[1];seen=set();rows=[]
    def visit(fn):
        if fn is None or id(fn) in seen:return
        if not isinstance(fn,types.FunctionType) or fn.__code__.co_argcount<3:raise ValueError('Unknown native observer callback')
        seen.add(id(fn));path=Path(fn.__code__.co_filename).resolve()
        if not path.is_relative_to(root):raise ValueError('External profiler cannot opt into Python-only observations')
        def check(value):
            if isinstance(value,str) and value in C_EVENTS:raise ValueError('C-event consumer cannot use the Python-only observer contract')
            if isinstance(value,(tuple,frozenset)):
                for part in value:check(part)
        for value in fn.__code__.co_consts:check(value)
        rows.append(dict(function=fn.__qualname__,file=str(path.relative_to(root)),source_sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        for name,cell in zip(fn.__code__.co_freevars,fn.__closure__ or ()):
            try:value=cell.cell_contents
            except ValueError:continue
            if name in ('previous','previous_profile','old','prev'):visit(value)
    visit(callback);return rows

@contextmanager
def python_observers_only(enabled=False):
    if not enabled:yield None;return
    previous=sys.getprofile()
    if getattr(previous,'_nikke_python_event_filter',False):yield None;return
    observers=observer_chain(previous);counts=dict(call=0,return_=0,c_call=0,c_return=0,c_exception=0)
    def filtered(frame,event,answer):
        if event=='call':counts['call']+=1
        elif event=='return':counts['return_']+=1
        else:
            if event not in counts:raise ValueError('Unknown profiler event: '+event)
            counts[event]+=1;return
        if previous is not None:previous(frame,event,answer)
    filtered._nikke_python_event_filter=True
    sys.setprofile(filtered)
    try:yield counts
    finally:
        current=sys.getprofile();sys.setprofile(previous)
        if current is not filtered:raise ValueError('Native profiler changed during simulation')
        RECEIPTS.append(dict(schema=1,observers=observers,event_counts=counts,python_observer_order_preserved=True,gpu_calls=0,calculation_verified=False))
