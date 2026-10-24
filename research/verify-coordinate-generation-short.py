"""Shared delayed coordinate target generations, retaining all prior76 inputs."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('coordinate_generation_parent',ROOT/'research/verify-coordinate-full-burst-short.py')
parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
from portable_coordinate_generation_cases import fixtures
SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
suite=parent.suite;cross=parent.cross;compile_case=parent.compile_case;compare=parent.compare


def verify_witness(case,result):
    label=case['name'].split('/')[-1];selected=result['coordinate_selection'];landings=result['coordinate_target_accounting']
    assert [row['generations'] for row in selected]==[[],[1,1],[1,1]]
    expected=[1,1,1,1]
    if label in ('reopened-parts','reopened-both','reopened-lifesteal','reopened-counter','reopened-destroyed'):expected=[1,1,2,2]
    elif label in ('reopened-interrupt','reopened-interrupt-lifesteal','mixed-pattern-generations'):expected=[1,1,2,1]
    assert [row['generation'] for row in landings]==expected,(case['name'],'landing generations')
    assert selected[-1]['time']<landings[-1]['time']
    if label.startswith('expired-'):
        stale=landings[2:4] if case['generation_witness']['kind']=='parts' else landings[2:3]
        assert all(not row['before_alive'] and row['pool_damage_delta']==row['pool_hits_delta']==0 for row in stale)
    if label=='reopened-counter':
        rows=[r for r in result['battle']['target_counters']['completions'] if r['name']=='generation-two-counter']
        assert len(rows)==1 and rows[0]['actor']['generation']==2 and rows[0]['impact']['damage']==900 and rows[0]['credit']==1
    if label=='reopened-destroyed':assert sum(row['event']=='destroy' for row in result['battle']['boss_log'])==4
    if label=='expired-counter-order':
        rows=[r for r in result['battle']['target_counters']['completions'] if r['name'].startswith('stale-')]
        assert [r['reason'] for r in rows]==['threshold','death'] and [r['credit'] for r in rows]==[2,2]
        assert rows[0]['time']==rows[1]['time']==landings[2]['time']
    return result


def native_reference(domain):
    result=parent.native_reference(domain)
    if domain[0].get('generation_witness'):verify_witness(domain[0],result)
    return result


def prepare():
    entries,_=parent.prepare()
    for case in fixtures():
        words,meta,bindings,descriptors=compile_case(case)
        entries.append((case['name'],words,(case,meta,bindings,descriptors)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


validate_rejection=parent.validate_rejection
