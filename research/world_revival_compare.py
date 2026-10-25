"""One saved-readback revival trace and allied-RNG comparison for both backends."""
import struct
from portable_revival_specs import BASE,TRACE,TRACE_COUNT,RNG
from portable_specs import LIMITS as L

def expected_revive(case,native):
    enabled=any(e.get('stat')=='revive' or e.get('persist_on_revive') for e in case['effects'])
    events=[];health={}
    if not enabled:return events
    for e in native['revival_events']:
        if e['kind']=='after-down':events.append(dict(kind=1,owner=e['owner'],time=e['time'],hp=0.,ammo=0))
        elif e['kind']=='after-revive':health[e['owner']]=e['state']['hp'][e['owner']]
        elif e['kind']=='action-revive':events.append(dict(kind=2,owner=e['owner'],time=e['time'],hp=health[e['owner']],ammo=e['ammo']))
    return events


def compare_revival_state(block,c,native):
    count=block[BASE+6];assert count<=TRACE_COUNT
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    events=[]
    for i in range(count):
        at=TRACE+i*8;assert block[at+7]==0
        events.append(dict(kind=block[at],owner=block[at+1],time=number(at+2),hp=number(at+4),ammo=block[at+6]))
    assert events==expected_revive(c,native),(c['name'],'revival trace',events,expected_revive(c,native))
    targets=[e for e in native['revival_events'] if e['kind']=='target' and e['random_after'] is not None]
    if targets:
        last=targets[-1]['random_after'];assert block[RNG]==last[-1] and list(block[RNG+8:RNG+8+624])==last[:-1],(c['name'],'independent allied RNG')
    assert block[BASE+5]==0 and not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096])
