"""One shared executor/adapter and independent native reader for CUDA/Metal."""
import array,copy,importlib.util,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts','tests')]
from portable_specs import LIMITS as L,FIELDS as F
from portable_effect_target_count_specs import compile_program,decode,SOURCE,STAT
from effect_target_count_policy import MODEL
from portable_effect_target_count_shared_cases import fixtures,native
import engine_worker
from test_target_counter_runtime import NAMES
s=importlib.util.spec_from_file_location('target_count_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
suite=SimpleNamespace(INPUT=L['INPUT_WORDS'],OUTPUT=L['OUTPUT_WORDS'],SOURCE=SOURCE)

def prepare():
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES];entries=[]
    for case in fixtures():
        w,m=compile_program(chars,list(zip(case['effects'],[NAMES[i] for i in case['owners']])),case['script'],[1000]*5,model=MODEL)
        entries.append((case['name'],w,(case,m)))
    original=entries[0][1]
    for name,offset,value in [('non-integral',L['DEFINITION_BASE']+F['VALUE'],0),('bad-name',L['DEFINITION_BASE']+F['TARGET_NAME'],256),('missing-query-limit',L['COMMAND_BASE']+8+6,0)]:
        w=list(original)
        if name=='non-integral':
            import struct
            w[offset:offset+2]=struct.unpack('<II',struct.pack('<d',1.5))
        else:w[offset]=value
        entries.append(('reject/'+name,w,None))
    data=array.array('I',[len(entries)])
    for _,w,_ in entries:data.extend(w)
    if sys.byteorder!='little':data.byteswap()
    return entries,data.tobytes()

def native_reference(domain):return native(domain[0])

def compare(words,domain):
    if words[0]!=0:raise AssertionError('Shared executor rejected named count: '+str(words[0]))
    observed=dict(queries=decode(words,domain[1]));expected=native_reference(domain)
    if observed!=expected:raise AssertionError((domain[0]['name'],observed,expected))
    return expected
