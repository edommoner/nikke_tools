"""Reuse complete world/native and named-state comparison for enemy_selection."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('enemy_selection_base',ROOT/'research/verify-world-projectile-short.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
from portable_input_aliases import group_entries,compare_aliases


def native_reference(domain):
    return compare_aliases(domain,lambda d:dict(zip(('battle','skill_trace'),suite.inspect_native(d[0]))))


def compare(block,domain):return compare_aliases(domain,lambda d:base.compare(block,d))


REJECTION_STAGES=dict(zip(('unknown-route','missing-rng','invalid-rng','rng-reserved','zero-count','count-overflow','no-combat','nan','no-actor-pool'),(404,404,404,12,404,11,0,404,404)))


def validate_rejection_stage(block,name):
    stage=REJECTION_STAGES[name.removeprefix('reject/enemy-selection-')]
    marker,actual=block[786416:786418]
    if actual!=stage or marker!=(0x57504144 if stage else 0):
        raise ValueError('Wrong admission stage for '+name)


def prepare():
    from portable_enemy_selection_cases import fixtures,negative_inputs
    entries=[]
    for case in fixtures():
        words,metadata,bindings=suite.compile_case(case)
        entries.append((case['name'],words,(case,metadata,bindings)))
    entries+=negative_inputs(suite.compile_case)
    entries=group_entries(entries)
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
