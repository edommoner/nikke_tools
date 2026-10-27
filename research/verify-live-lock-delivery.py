"""Shared real-queue delivery under an explicit, partial recipient policy."""
import array,copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
spec=importlib.util.spec_from_file_location('live_delivery_parent',ROOT/'research/verify-lock-packets.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from live_lock_delivery_policy import MODEL
from world_lock_packet_native import observe
SOURCE='gpu/world_lock_delivery_entry.slang';INPUT=parent.INPUT;OUTPUT=parent.OUTPUT
suite=SimpleNamespace(SOURCE=SOURCE,INPUT=INPUT,OUTPUT=OUTPUT);cross=parent.cross

def fixtures():
    rows=[]
    for index in (0,1,3):
        c=copy.deepcopy(parent.fixtures()[index]);c['name']=c['name'].replace('lock-packet/','live-lock-delivery/');rows.append(c)
    c=copy.deepcopy(rows[0]);c['name']='live-lock-delivery/health-counter'
    from portable_burst_recipient_cases import instant
    from world_enemy_attack_cases import field
    from target_counter_cases import marker
    counter=marker(threshold=1,attackers='owner',actor=dict(kind='add',identity=0,generation=1))
    counter['target']='boss';counter['trigger']['timing']=['battle_start'];counter['target_counter']['families']=['skill']
    c['effects'].extend([instant('current_hp_reduce',80,'self','wound'),field('lifesteal_pct',10,'self','life'),counter])
    c['owners'].extend([0,0,0]);c['environment']['allies'][0]['base_hp']=1e9;rows.append(c)
    return rows

compile_case=parent.compile_case
def native_reference(domain):return observe(domain[0],delivery_model=MODEL)
def compare(block,domain):
    candidates=[];n=observe(domain[0],delivery_model=MODEL,candidate_observer=lambda values:candidates.append(tuple(values)))
    return parent.parent.parent.compare_observed(block,domain,n,candidates,manual=bool(domain[0].get('physical_cover_composition')),packet_bindings=True)

def prepare():
    entries=[]
    for c in fixtures():
        words,meta,bindings=compile_case(c);entries.append((c['name'],words,(c,meta,bindings)))
    c=parent.fixtures()[2];words,_,_=compile_case(c)
    entries.append(('reject/live-lock-delivery/unresolved-death-policy',words,None))
    entries.extend((name.replace('reject/lock-packet/','reject/live-lock-delivery/'),words,None) for name,words,domain in parent.prepare()[0] if domain is None)
    raw=array.array('I',[len(entries)])
    for _,words,_ in entries:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return entries,raw.tobytes()
