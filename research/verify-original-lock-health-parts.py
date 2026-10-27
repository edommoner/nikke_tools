"""Original real roster: reached parts, injury, healing and HP-conditioned burst."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
s=importlib.util.spec_from_file_location('health_parts_parent',ROOT/'research/verify-original-lock-composition.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_heavyarms_original_composition import prepare_case
from portable_heal_share_trace import gpu_records,COUNT
SOURCE='gpu/world_original_lock_health_parts_entry.slang'
suite=SimpleNamespace(SOURCE=SOURCE,INPUT=109536,OUTPUT=1310720);cross=parent.cross;compile_case=parent.compile_case

def fixtures():
    specs=[dict(parts=True),dict(parts=True,break_parts=True),dict(injury=True),dict(injury=True,mary_first=True),dict(injury=True,mary_first=True,mary_low=True),dict(parts=True,injury=True,mary_first=True),dict(parts=True,injury=True,mary_first=True,adds=3)]
    rows=[]
    for spec in specs:
        c,_=prepare_case(30,**spec)
        c.update(observe_original_healing=True,observe_heal_sources=True,original_health_parts_contract=spec)
        rows.append(c)
    return rows

def verify_contract(c,n):
    spec=c['original_health_parts_contract'];battle=n['battle']
    calls=n['healing_calls']
    if len(calls)>COUNT:raise AssertionError('Complete healing history exceeds existing trace capacity')
    if spec.get('parts'):
        parts=battle['target_counters']['part_extra']
        if len(parts)!=2 or any(p['extra_hits']<=0 or p['extra_dealt']<=0 for p in parts):raise AssertionError('Actual original attacks must reach both declared PART actors')
        if spec.get('break_parts') and not any(row['event']=='destroy' and row['pattern']=='original-parts' for row in battle['boss_log']):raise AssertionError('Breakable parts must be destroyed by actual original packets')
    if spec.get('injury'):
        if any(a['down'] or a['received_damage']<=0 for a in battle['allies']):raise AssertionError('Every real ally must be injured and remain alive')
        if not any(a['hp']>a['max_hp']-a['received_damage'] for a in battle['allies']):raise AssertionError('Original healing must restore actual HP')
        if not any(row[0]==6 for row in calls):raise AssertionError('Actual heal-received notification must be observed')
        if not any(hit['pattern']=='original-after-heal' for hit in battle['hits']):raise AssertionError('Conditional defense must have a real later attack consumer')
    return n

def native_reference(domain,**kwargs):return verify_contract(domain[0],parent.native_reference(domain,**kwargs))
def compare(block,domain):
    n=parent.compare(block,domain)
    if gpu_records(block,observe_heal_sources=True)!=n['healing_calls']:raise AssertionError('Complete healing call/portion/notification history changed')
    return verify_contract(domain[0],n)

def prepare():
    return parent.prepare(cases=fixtures())
