"""All native-routing53 retained, plus lossless long histories and flag rejection."""
import array,copy,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from portable_long_group_cases import fixtures
from portable_long_group_contracts import verify
from world_battle_native_route_native import observe
from portable_battle_attack_group_input import compile_battle
spec=importlib.util.spec_from_file_location('long_group_parent',ROOT/'research/verify-world-attack-group-native-route-short.py');parent=importlib.util.module_from_spec(spec);spec.loader.exec_module(parent)
SOURCE=parent.SOURCE;INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS
STRICT_WIRE_DIMENSIONS=True;suite=parent.suite;cross=parent.cross
def native_reference(domain):
    if domain[0].get('group_history')!='compact':return parent.native_reference(domain)
    n,_=observe(domain[0]);verify(domain[0],n);return n
suite.inspect_native=lambda case:native_reference((case,))
def prepare():
    entries,_=parent.prepare()
    for case in fixtures():
        prepared=engine_worker.evaluate(dict(case['body'],_portable_static_inputs=True))
        words,metadata=compile_battle(prepared,routing=case['routing'],declared_effects=case.get('declared_effects',[]),group_history='compact')
        prepared=copy.deepcopy(prepared)
        for effect in case.get('declared_effects',[]):prepared['effects'].append(dict(effect=copy.deepcopy(effect),owner=case['body']['squad'][0]))
        entries.append((case['name'],words,(case,prepared,words,metadata)))
    words=list(entries[0][1]);words[104403]=2;entries.append(('reject/attack-group-unknown-history',words,None))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
def compare(block,domain):return parent.shared.compare(block,domain,native=native_reference(domain))
validate_rejection=parent.validate_rejection
