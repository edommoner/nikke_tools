"""Compose unchanged comparators into one input/dispatch/pipeline regression."""
import array
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


ADAPTERS={
    'readiness':module('regression_readiness','research/verify-world-readiness-short.py'),
    'stun':module('regression_stun','research/verify-world-stun-short.py'),
    'roster':module('regression_roster','research/verify-world-roster-regression-short.py'),
    'skill-cooldown':module('regression_skill_clock','research/verify-world-skill-cooldown-short.py'),
    'healing-storage':module('regression_healing_storage','research/verify-world-healing-storage-short.py'),
    'trigger-reduction':module('regression_trigger_reduction','research/verify-world-trigger-reduction-short.py'),
    'skill-critical':module('regression_skill_critical','research/verify-world-skill-critical-short.py'),
    'skill-interval':module('regression_skill_interval','research/verify-world-skill-interval-short.py'),
    'skill-interval-flat':module('regression_skill_interval_flat','research/verify-world-skill-interval-flat-short.py'),
    'lazy-bank':module('regression_lazy_bank','research/verify-world-lazy-bank-short.py'),
    'base-copy':module('regression_base_copy','research/verify-world-base-copy-short.py'),
    'persona':module('regression_persona','research/verify-world-persona-short.py'),
    'named-magnitude':module('regression_named_magnitude','research/verify-world-named-magnitude-short.py'),
    'enemy-selection':module('regression_enemy_selection','research/verify-world-enemy-selection-short.py'),
    'attack-magnitude':module('regression_attack_magnitude','research/verify-world-attack-magnitude-short.py'),
    'revive':module('regression_revival','research/verify-world-revive-short.py'),
}
cross=ADAPTERS['readiness'].cross
suite=SimpleNamespace(INPUT=104400,OUTPUT=786432)


def combine(adapters):
    entries=[]
    for name,adapter in adapters.items():
        if adapter.suite.INPUT!=suite.INPUT or adapter.suite.OUTPUT!=suite.OUTPUT:
            raise ValueError('Regression adapters must share exact wire strides')
        rows,data=adapter.prepare()
        if len(data)!=(1+len(rows)*suite.INPUT)*4 or int.from_bytes(data[:4],'little')!=len(rows):
            raise ValueError('Regression adapter input/header mismatch')
        for i,(label,words,domain) in enumerate(rows):
            if len(words)!=suite.INPUT:raise ValueError('Regression input row stride mismatch')
            # Retain compact native-endian words rather than every Python list.
            # Check the same canonical little-endian wire one row at a time.
            compact=array.array('I',words)
            wire=compact if sys.byteorder=='little' else array.array('I',compact)
            if sys.byteorder!='little':wire.byteswap()
            start=4+i*suite.INPUT*4
            if wire.tobytes()!=data[start:start+suite.INPUT*4]:raise ValueError('Regression adapter input/header mismatch')
            entries.append((name+'/'+label,compact,None if domain is None else (name,domain)))
        del rows,data
    if len({row[0] for row in entries})!=len(entries):raise ValueError('Duplicate regression case identity')
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def prepare():return combine(ADAPTERS)


def native_reference(domain):
    name,inner=domain
    if hasattr(ADAPTERS[name],'native_reference'):return ADAPTERS[name].native_reference(inner)
    return dict(zip(('battle','skill_trace'),ADAPTERS[name].suite.inspect_native(inner[0])))


def compare(block,domain):
    name,inner=domain
    return ADAPTERS[name].compare(block,inner)


def validate_rejection(block,name):
    family,label=name.split('/',1);adapter=ADAPTERS[family]
    if hasattr(adapter,'validate_rejection'):adapter.validate_rejection(block,label)
