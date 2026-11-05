"""Retain coordinate24 and connect DoT clocks to the same coordinate packets."""
import array,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_coordinate_dot_cases import fixtures
spec=importlib.util.spec_from_file_location('coordinate_dot_parent',ROOT/'research/verify-coordinate-skill-short.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True;cross=parent.cross
suite=SimpleNamespace(INPUT=INPUT_WORDS,OUTPUT=OUTPUT_WORDS,inspect_native=lambda case:native_reference((case,)))

def prepare():
    entries,_=parent.prepare()
    for case in fixtures():
        words,meta,bindings,descriptors=parent.compile_case(case);entries.append((case['name'],words,(case,meta,bindings,descriptors)))
    seed=entries[24][1];case,meta,_,_=entries[24][2];source=next(i for i,e in enumerate(case['effects']) if e['type']=='damage');row=meta['binding_source_indices'].index(source)
    L,F=parent.L,parent.F
    words=list(seed);at=L['DEFINITION_BASE']+row*L['DEFINITION_WORDS']+F['INTERVAL'];words[at:at+2]=[0,0];entries.append(('reject/coordinate-dot-no-clock',words,None))
    words=list(seed);words[L['DAMAGE_DEFINITION_BASE']+row*L['DAMAGE_DEFINITION_WORDS']+6]=1;entries.append(('reject/coordinate-dot-pending-unconnected',words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()

def verify_result(domain,result):
    case=domain[0]
    if case['contract'].get('dot_counter'):
        rows=result['battle']['target_counters']['completions'];assert len(rows)==1 and rows[0]['reason']=='threshold' and rows[0]['credit']==2 and rows[0]['impact']['family']==2 and rows[0]['actor']['kind']==1
    if case['name']=='coordinate-dot/reopened-generation-two':assert [s['generations'] for s in result['coordinate_selection']]==[[1,1],[2,2],[]]
    if case['name']=='coordinate-dot/birth-after-created-final-tick':
        last=result['skill_trace'][-1];assert last['created']<.21<last['landed'];assert result['coordinate_selection'][-1]['targets']==['near','far']
    return result

def native_reference(domain):return verify_result(domain,parent.native_reference(domain))
def compare(block,domain):return verify_result(domain,parent.compare(block,domain))
def validate_rejection(block,name):
    if name.startswith('reject/coordinate-dot-'):assert block[0]==64
    else:parent.validate_rejection(block,name)
