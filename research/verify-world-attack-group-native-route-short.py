"""Native routing20 plus unchanged declared routing32; one shared comparer."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
from portable_battle_native_route_cases import fixtures
from world_battle_native_route_native import observe
from portable_battle_native_route_contracts import verify
from portable_battle_attack_group_input import compile_battle
import engine_worker
spec=importlib.util.spec_from_file_location('native_route_shared_adapter',ROOT/'research/verify-world-attack-group-battle-short.py')
shared=importlib.util.module_from_spec(spec);spec.loader.exec_module(shared)
SOURCE=shared.SOURCE;INPUT_WORDS=shared.INPUT_WORDS;OUTPUT_WORDS=shared.OUTPUT_WORDS
STRICT_WIRE_DIMENSIONS=True
suite=shared.suite;cross=shared.cross

def native_reference(domain):
    if domain[0]['routing']!='native':return shared.native_reference(domain)
    native,_=observe(domain[0]);verify(domain[0],native);return native
suite.inspect_native=lambda case: native_reference((case,))

def prepare():
    entries,_=shared.prepare()
    for case in fixtures():
        prepared=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
        words,metadata=compile_battle(prepared,routing='native',declared_effects=case.get('declared_effects',[]))
        prepared=copy.deepcopy(prepared)
        for effect in case.get('declared_effects',[]):prepared['effects'].append(dict(effect=copy.deepcopy(effect),owner=case['body']['squad'][0]))
        entries.append((case['name'],words,(case,prepared,words,metadata)))
    words=list(entries[0][1]);words[104401]=3
    entries.append(('reject/attack-group-unknown-routing',words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()

def compare(block,domain):return shared.compare(block,domain,native=native_reference(domain))
validate_rejection=shared.validate_rejection
