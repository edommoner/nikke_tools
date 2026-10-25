"""Fresh native creation receipts for one live preflight/comparison owner."""
import contextlib,copy
from pathlib import Path
from unittest.mock import patch

ROUTES=(('manual_controls','verify-coordinate-manual-short.py'),
        ('sampled_delivery','verify-coordinate-sampled-delivery-short.py'),
        ('sampled_vital','verify-coordinate-sampled-vital-short.py'),
        ('sampled_burst','verify-coordinate-sampled-burst-short.py'),
        ('sampled_skill','verify-coordinate-sampled-skill-short.py'),
        ('sampled_parent','verify-coordinate-sampled-parent-short.py'))

def choose(manual,domain):
    case=domain[0];node=manual
    for flag,name in ROUTES:
        if Path(node.__file__).name!=name:raise ValueError('Unreviewed coordinate native comparison chain')
        if case.get(flag):return node
        node=node.parent
    if Path(node.__file__).name!='verify-coordinate-sampled-battle-short.py':raise ValueError('Unreviewed coordinate native base comparator')
    return node

def needs_receipts(domain):return any(domain[0].get(flag) for flag,_ in ROUTES[:-1])

@contextlib.contextmanager
def capture(domain):
    if not needs_receipts(domain):yield None;return
    # Reuse the observation already performed by native_reference. Installing
    # another sys.setprofile observer would repeat all-frame instrumentation.
    import world_coordinate_sampled_skill_native as source
    original=source.creation_indices;receipts=[];calls=0
    def signature(case):
        return (case['name'],[(i,e['name']) for i,e in enumerate(case['effects']) if e.get('type')=='damage'],
                bool(case.get('sampled_burst')),bool(case.get('coordinate_packet_trace')))
    expected=signature(domain[0])
    @contextlib.contextmanager
    def observed(case):
        nonlocal calls
        if signature(case)!=expected:raise ValueError('Unexpected native creation observation case')
        calls+=1
        if calls!=1:raise ValueError('Repeated native creation observation')
        with original(case) as rows:yield rows
        receipts.extend(copy.deepcopy(rows))
    with patch.object(source,'creation_indices',observed):yield receipts
    if calls!=1:raise ValueError('Missing native creation observation')

def validate(domain,native,receipts):
    if not needs_receipts(domain):
        if receipts is not None:raise ValueError('Unexpected coordinate creation receipts')
        return
    from world_coordinate_sampled_skill_native import trace_view
    trace_view(native['skill_trace'],receipts)

@contextlib.contextmanager
def restore(domain,receipts):
    if not needs_receipts(domain):
        if receipts is not None:raise ValueError('Unexpected coordinate creation receipts')
        yield;return
    import world_coordinate_sampled_skill_native as source
    calls=0
    @contextlib.contextmanager
    def saved(case):
        nonlocal calls
        if case is not domain[0]:raise ValueError('Unexpected coordinate creation receipt consumer')
        calls+=1
        if calls!=1:raise ValueError('Repeated coordinate creation receipt consumer')
        yield copy.deepcopy(receipts)
    with patch.object(source,'creation_indices',saved):yield
    if calls!=1:raise ValueError('Missing coordinate creation receipt consumer')
