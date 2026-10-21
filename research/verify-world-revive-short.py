"""Shared revival fixtures/native contracts; one execution and comparison for both GPUs."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('revival_base',ROOT/'research/verify-world-projectile-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_revival_specs import BASE,TRACE,TRACE_COUNT,RNG
from portable_specs import LIMITS as L,FIELDS as F
from portable_revive_cases import fixtures
from world_revive_native import observe
from portable_revive_contracts import verify


def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    seed=next(w for name,w,_ in entries if name=='revive-synchronous');row=2;d=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS'];mode=L['MODE_BASE']+row*L['MODE_WORDS'];recipient=L['RECIPIENT_BASE']+row*8
    for label,at,value in [('zero',d+F['VALUE']+1,0),('negative',d+F['VALUE']+1,0xbff00000),('nan',d+F['VALUE']+1,0x7ff80000),('infinite',d+F['VALUE']+1,0x7ff00000),('missing-seed',mode,0),('wrong-kind',d+F['KIND'],4),('instant-persist',d+F['FLAGS'],1024),('zero-count',recipient+1,0),('invalid-recipient-mask',recipient+2,32)]:
        words=list(seed);words[at]=value
        entries.append(('reject/revive-'+label,words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def expected_revive(case,native):
    enabled=any(e.get('stat')=='revive' or e.get('persist_on_revive') for e in case['effects'])
    events=[];health={}
    if not enabled:return events
    for e in native['revival_events']:
        if e['kind']=='after-down':events.append(dict(kind=1,owner=e['owner'],time=e['time'],hp=0.,ammo=0))
        elif e['kind']=='after-revive':health[e['owner']]=e['state']['hp'][e['owner']]
        elif e['kind']=='action-revive':events.append(dict(kind=2,owner=e['owner'],time=e['time'],hp=health[e['owner']],ammo=e['ammo']))
    return events


def reference_result(case,native,trace):
    targets=[e for e in native['revival_events'] if e['kind']=='target' and e['random_after'] is not None]
    events=expected_revive(case,native)
    native.pop('revival_events')
    return dict(battle=native,skill_trace=trace,revival_trace=events,allied_rng=targets[-1]['random_after'] if targets else None)


def native_reference(domain):
    c,_,_=domain;native,trace=observe(c);verify(c,native)
    return reference_result(c,native,trace)


def compare(block,domain):
    c,m,b=domain;native,trace=observe(c);verify(c,native)
    actual=suite.decoded(block,m,c,b)
    for k in native:
        if k not in ('scope','revival_events'):assert actual[k]==native[k],(c['name'],k)
    assert suite.reload.charge.team.skill_trace(block,m)==trace
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
    return reference_result(c,native,trace)


def validate_rejection_stage(block,name):
    expected=403 if name.endswith(('zero-count','invalid-recipient-mask')) else 26
    if block[786416]!=0x57504144 or block[786417]!=expected:
        raise ValueError('Revival rejection missed intended stage: '+name)
