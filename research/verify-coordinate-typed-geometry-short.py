"""Superset of original coordinate/typed battles and live spatial target selection."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('typed_geometry_parent',ROOT/'research/verify-coordinate-typed-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from typed_geometry_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from portable_coordinate_typed_input import compile_coordinate_typed
from portable_coordinate_typed_specs import SOURCE,INPUT_WORDS,OUTPUT_WORDS
from world_destructible_weapon_roster_native import capture_typed,snapshot_typed
BASE_NATIVE=parent.native_reference
suite=parent.suite;cross=parent.cross;STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows,_=parent.prepare()
    for row in fixtures():
        c,p=prepare_case(row);c['coordinate_packet_history']='ordered-sha256-v1';c['body']=copy.deepcopy(row['body'])
        for key in ('declared_effects','typed_bindings','max_attacks','character','declared_projectile_probe','probe_kind','typed_geometry','expected_handles'):c[key]=copy.deepcopy(row[key])
        c['coordinate_typed_probe']=True;c['spatial_typed_probe']=True;c['probe_source']=len(p['effects'])
        for effect in row['declared_effects']:
            p['effects'].append(dict(owner=c['names'][0],effect=copy.deepcopy(effect)));c['effects'].append(copy.deepcopy(effect));c['owners'].append(0)
        w,m,b,d=compile_coordinate_typed(p,c['typed_bindings'],c['probe_source'],probe_kind=c['probe_kind'],max_attacks=c['max_attacks'],geometry=c['typed_geometry']);rows.append((c['name'],w,(c,m,b,d)))
    seed=rows[-len(fixtures())][1]
    for label,offset,value in [('magic',0,1),('version',1,2),('count',2,129),('kind',3,4),('grow-negative-high',9,0xbff00000),('header-reserved',10,1),('shape-kind',16,3),('shape-reserved',17,1),('shape-radius-zero-low',22,0),('shape-unused-tail',16+2*18,1)]:
        w=list(seed)
        if label=='shape-radius-zero-low':w[109968+22:109968+24]=[0,0]
        else:w[109968+offset]=value
        rows.append(('reject/typed-geometry/'+label,w,None))
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()

def native_reference(domain):
    if not domain[0].get('spatial_typed_probe'):return BASE_NATIVE(domain)
    c=domain[0]
    with capture_typed(c) as (data,samples,heals):n=parent.parent.native_reference(domain)
    typed=snapshot_typed(c,data,samples,heals,{},[]);n['typed_target_battle']={k:v for k,v in typed.items() if k not in ('battle','projectile_shots')}
    attacks=typed['typed']['attacks'];n['skill_trace'],suppressed=parent.partition_trace(n['skill_trace'],attacks,c['probe_source'],0);n['typed_target_battle']['suppressed_body_trace']=suppressed
    handles=[v['handle'] for r in attacks for v in r['receipts']];assert handles==c['expected_handles'],(c['name'],handles,c['expected_handles'])
    assert all(r['completed'] and len(r['receipts'])==1 and r['receipts'][0]['delivered'] for r in attacks)
    assert len(samples)==len(attacks)==len(typed['packet_samples'])
    assert all(r['source']==c['probe_source'] and r['coefficient']==100. for r in typed['packet_samples'])
    if handles:assert all(r['modifier']>0 for r in samples),'Original modifier must contribute to spatial damage'
    return n

def compare(block,domain):
    # Reuse the same full coordinate and typed comparator with this fresh oracle.
    from unittest.mock import patch
    with patch.object(parent,'native_reference',native_reference):return parent.compare(block,domain)

def validate_rejection(block,name):assert name.startswith('reject/typed-geometry/') and block[0]==64,(name,block[0])
