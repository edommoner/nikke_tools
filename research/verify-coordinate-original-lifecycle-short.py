"""Original alternate DoT sources through the same CUDA/Metal executor."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('lifecycle_original_parent',ROOT/'research/verify-coordinate-original-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_original_lifecycle_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_original_periodic_lifecycle import capture
suite=parent.suite;cross=parent.cross;SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['lifecycle_witness']=row['lifecycle_witness'];w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,words,_ in rows:raw.extend(words)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def native_reference(domain):
    with capture(domain[0]) as activations:n=parent.native_reference(domain)
    n['original_periodic_activations']=activations
    verify_witness(domain[0],n)
    return n

def verify_witness(case,n):
    rows=n['original_periodic_activations'];alternate=[r for r in rows if r['row']==1]
    label=case['lifecycle_witness'];deaths=[r for r in n['battle']['boss_log'] if r['event']=='destroy']
    assert rows and all(r['owner']==0 for r in rows),'Actual primary DoT sources required'
    if label=='death-before-dot':
        assert len(deaths)==2 and not alternate
        assert max(r['time'] for r in deaths)<rows[0]['time']
    else:
        assert len(alternate)==(2 if label=='death-refresh' else 1),'Both actual death notifications or burst cast must fire original source1'
        if label=='death-refresh':
            assert len(deaths)==2 and all(r['time']<=alternate[0]['time'] for r in deaths)
        for r in alternate:
            assert len(r['before'])==len(r['after'])==1,'Same-label DoT must retain one carrier'
            before=r['before'][0];after=r['after'][0]
            assert before['row']==after['row']==0 and before['owner']==after['owner']==0
            assert before['activated']==after['activated'] and before['timer'][0]==after['timer'][0],'Refresh must preserve tick phase'
            assert after['expires']>=before['expires'] and after['timer'][1]==after['expires']
        assert any(r['after'][0]['expires']>r['before'][0]['expires'] for r in alternate),'Alternate source must really extend expiry'
    return True

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    from portable_runtime import decode
    actual=decode(block[:159744],domain[1])
    for source in (0,1):
        bindings=[i for i,j in enumerate(domain[1]['binding_source_indices']) if j==source]
        assert len(bindings)==1,'Each original DoT source needs one exact binding'
        timer=actual['timers'][bindings[0]]
        assert timer['activations']==sum(r['row']==source for r in n['original_periodic_activations']),'GPU must execute each actual original activation, including aliases'
        if source==1:assert not timer['active'],'Alternate source must refresh the existing carrier, not duplicate it'
    return n

def validate_rejection(block,name):raise AssertionError('Original lifecycle definitions cannot be discarded')
