"""Shared sampled live weapons and health; reuse the complete burst verifier."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('sampled_vital_parent',ROOT/'research/verify-coordinate-sampled-burst-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_sampled_vital_cases import fixtures
from world_coordinate_sampled_vital_native import observe
from world_coordinate_aim_native import capture
from portable_burst_recipient_cases import instant
SOURCE='gpu/world_coordinate_sampling_vital_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;compile_case=parent.compile_case

def prepare():
    rows,_=parent.prepare()
    for c in fixtures():
        w,m,b,d=compile_case(c);rows.append((c['name'],w,(c,m,b,d)))
    for stat in ('ammo_charge_flat','burst_cooldown_reduce'):
        c=copy.deepcopy(fixtures()[0]);c['effects'].append(instant(stat,1,'self','unsupported'));c['owners'].append(0);w,_,_,_=compile_case(c);rows.append(('reject/sampled-vital/'+stat,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
def native_reference(domain):
    if not domain[0].get('sampled_vital'):return parent.native_reference(domain)
    with capture(domain[0]) as aim:n,t=observe(domain[0])
    n['coordinate_aim']=aim;return n

def compare(block,domain):
    if not domain[0].get('sampled_vital'):return parent.compare(block,domain)
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    return n

def validate_rejection(block,name):
    if name.startswith('reject/sampled-vital/'):assert block[0]==64
    else:parent.validate_rejection(block,name)
