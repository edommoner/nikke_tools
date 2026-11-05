"""Complete real Peony profiles; reuse roster compiler and full native comparator."""
import array
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
real=module('lost_hp_real_oracle','research/verify-world-projectile-rosters.py')
cross=module('lost_hp_cross','research/summarize-portable-cross-gpu.py')
suite=SimpleNamespace(INPUT=real.INPUT_WORDS,OUTPUT=real.OUTPUT_WORDS,
                      inspect_native=lambda case:real.native_reference(case['body']))

def prepare():
    entries=[]
    for stage in range(4):
        for duration in (3,30):
            body=dict(real.body_for(real.policy.roster_for('목단'),duration),burst_gauge_mode='accumulate')
            body['profile']['chars']['목단']['favorite_stage']=stage
            if stage:body['profile']['chars']['목단']['collection_stage']='SR15'
            body['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=1,
                spec=dict(atk=300000,coeff=100,target='all',hits=3,interval=1,pierce=True))]
            prepared=real.engine_worker.evaluate(dict(body,_portable_static_inputs=True))
            words,metadata=real.compile_projectile_battle(prepared)
            case=dict(character='목단',favorite_stage=stage,duration=duration,body=body)
            entries.append((f'peony-{stage}-{duration}',words,(case,prepared,words,metadata)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()

def compare(block,domain):
    if block[0]!=0:raise ValueError('GPU rejected real input: status '+str(block[0]))
    case,prepared,words,metadata=domain
    native,shots=real.native_reference(case['body'])
    actual,events,omitted,diff=real.compare(block,prepared,(words,metadata),native,shots)
    if block[0]!=0 or diff:raise ValueError(str(dict(status=block[0],difference_count=len(diff),first_differences=diff[:8])))
    return dict(battle=native,skill_trace=shots)
