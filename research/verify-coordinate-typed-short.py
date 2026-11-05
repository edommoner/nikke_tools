"""Shared coordinate resident and typed Frame entry; full original battle parity."""
import array,copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('coordinate_typed_parent',ROOT/'research/verify-coordinate-original-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_typed_input import compile_coordinate_typed
from portable_coordinate_typed_specs import SOURCE,INPUT_WORDS,OUTPUT_WORDS,COORDINATE_OUTPUT_WORDS
from portable_coordinate_original_cases import prepare_case
from coordinate_typed_cases import fixtures
from world_destructible_weapon_roster_native import capture_typed,snapshot_typed
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS);STRICT_WIRE_DIMENSIONS=True;cross=parent.cross
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT

def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['coordinate_packet_history']='ordered-sha256-v1';c['body']=copy.deepcopy(row['body'])
        if row.get('declared_effects'):
            c.update({k:copy.deepcopy(row[k]) for k in ('declared_effects','typed_bindings','max_attacks','character','declared_projectile_probe')});c['probe_kind']=row.get('probe_kind',2);c['coordinate_typed_probe']=True;c['probe_source']=len(p['effects'])
            for effect in row['declared_effects']:
                p['effects'].append(dict(owner=row.get('probe_owner',c['names'][0]),effect=copy.deepcopy(effect)));c['effects'].append(copy.deepcopy(effect));c['owners'].append(c['names'].index(row.get('probe_owner',c['names'][0])))
            w,m,b,d=compile_coordinate_typed(p,row['typed_bindings'],c['probe_source'],probe_kind=c['probe_kind'],max_attacks=c['max_attacks'])
        else:w,m,b,d=compile_coordinate_typed(p)
        rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def partition_trace(trace,attacks,source,owner):
    selected=[r for r in trace if r['row']==source];rest=[r for r in trace if r['row']!=source]
    assert len(selected)==len(attacks),'Every suppressed body observation needs one typed attack'
    for row,attack in zip(selected,attacks,strict=True):
        assert row['created']==row['landed']==attack['time'] and row['amount']==attack['damage'] and attack['owner']==owner and row['hit']==row['hits']==1 and attack['completed'],'Exact declared typed packet identity required'
    return rest,selected

def native_reference(domain):
    c=domain[0]
    if not c.get('coordinate_typed_probe'):return parent.native_reference(domain)
    with capture_typed(c) as (data,samples,heals):n=parent.native_reference(domain)
    typed=snapshot_typed(c,data,samples,heals,{},[])
    n['typed_target_battle']={k:v for k,v in typed.items() if k not in ('battle','projectile_shots')}
    n['skill_trace'],suppressed=partition_trace(n['skill_trace'],typed['typed']['attacks'],c['probe_source'],c['owners'][c['probe_source']]);n['typed_target_battle']['suppressed_body_trace']=suppressed
    assert typed['packet_samples'] and all(r['source']==c['probe_source'] and r['coefficient']==100. for r in typed['packet_samples'])
    attacks=typed['typed']['attacks'];samples=typed['modifier_samples']
    assert len(samples)==len(attacks) and all(r['completed'] and r['receipts'] and all(v['handle'][0]==c['probe_kind'] and v['delivered'] for v in r['receipts']) for r in attacks)
    if c['character'] in ('클레이','미사토') and c['duration']==3:assert all(r['modifier']==0 for r in samples)
    else:assert any(r['modifier']>0 for r in samples),'Original target modifier must contribute in the actual coordinate battle'
    return n

def compare(block,domain):
    from portable_coordinate_typed_specs import audit_reserved
    audit_reserved(block)
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    if domain[0].get('coordinate_typed_probe'):
        from world_coordinate_sampled_skill_native import trace_view
        c=domain[0];typed_indices=[r for r in indices if r['row']==c['probe_source']];trace_view(n['typed_target_battle']['suppressed_body_trace'],typed_indices);indices=[r for r in indices if r['row']!=c['probe_source']]
    parent.compare_observed(block[:COORDINATE_OUTPUT_WORDS],domain,n,indices)
    if domain[0].get('coordinate_typed_probe'):
        from portable_destructible_roster_skill_comparison import prior
        c,m,_,_=domain;typed=n['typed_target_battle'];packets=typed['packet_samples']
        view=[0]*786432+list(block[COORDINATE_OUTPUT_WORDS:])
        got=prior.prior.battle.decode(view,(c,m,()),sampled_coefficients=[r['coefficient'] for r in packets],sampled_rows=[r['source'] for r in packets],sampled_packets=[r['mode_skill'] for r in packets],sampled_skill_metadata=[[0]*5 for r in packets])
        assert got==typed['typed'],(c['name'],got,typed['typed'])
    else:assert not any(block[COORDINATE_OUTPUT_WORDS:]),'Disabled typed bank must remain zero'
    return n

def validate_rejection(block,name):raise AssertionError('No original coordinate definition may be discarded')
