"""Shared per-shot event admission and full-native battle comparison."""
import array,importlib.util,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('pellet_shot_battle_base',ROOT/'research/verify-world-heal-share-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_pellet_shot_cases import fixtures
from world_pellet_shot_native import observe
from portable_pellet_shot_contracts import verify
from portable_specs import LIMITS as L
from portable_runtime import double_words


def prepare():
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case);entries.append((case['name'],words,(case,metadata,bindings)))
    seed=entries[0][1];at=L['EVENT_BASE']+L['EVENT_WORDS']
    mutations=[('no-combat',[(3,0)]),('mode',[(at+3,1)]),('zero-id',[(at+4,0)]),('sparse-id',[(at+4,2)]),('oversized-id',[(at+4,2049)]),('payload',[(at+5,1)]),('passive',[(at+6,1)]),('stage',[(at+7,0xffffffff)])]
    for name,value in [('fraction',5.5),('too-negative',-2147483649),('too-positive',2147483648),('nan',float('nan')),('infinite',float('inf'))]:
        mutations.append((name,list(zip((at+1,at+2),struct.unpack('<II',struct.pack('<d',value))))))
    for label,edits in mutations:
        words=list(seed)
        for offset,value in edits:words[offset]=value
        entries.append(('reject/pellet-shot-'+label,words,None))
    aliases=next(entry for entry in entries if entry[0]=='pellet-shot-raw-aliases')[1]
    words=list(aliases);words[at+1:at+3]=double_words(6);entries.append(('reject/pellet-shot-numeric-order',words,None))
    duplicates=next(entry for entry in entries if entry[0]=='pellet-shot-duplicate-descriptor')[1]
    words=list(duplicates);words[at+9:at+11]=double_words(6);entries.append(('reject/pellet-shot-id-conflict',words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def native_reference(domain):
    native,trace=observe(domain[0]);verify(domain[0],native);native.pop('pellet_shot')
    return dict(battle=native,skill_trace=trace)
def compare(block,domain):return base.compare_expected(block,domain,native_reference(domain))
def validate_rejection(block,name):assert name.startswith('reject/pellet-shot-') and block[0]==64
