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
}
cross=ADAPTERS['readiness'].cross
suite=SimpleNamespace(INPUT=104400,OUTPUT=786432)


def combine(adapters):
    entries=[]
    for name,adapter in adapters.items():
        if adapter.suite.INPUT!=suite.INPUT or adapter.suite.OUTPUT!=suite.OUTPUT:
            raise ValueError('Regression adapters must share exact wire strides')
        rows,data=adapter.prepare()
        packed=array.array('I',[len(rows)])
        for _,words,_ in rows:
            if len(words)!=suite.INPUT:raise ValueError('Regression input row stride mismatch')
            packed.extend(words)
        if sys.byteorder!='little':packed.byteswap()
        if packed.tobytes()!=data:raise ValueError('Regression adapter input/header mismatch')
        entries.extend((name+'/'+label,words,None if domain is None else (name,domain))
                       for label,words,domain in rows)
    if len({row[0] for row in entries})!=len(entries):raise ValueError('Duplicate regression case identity')
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()


def prepare():return combine(ADAPTERS)


def native_reference(domain):
    name,inner=domain
    return dict(zip(('battle','skill_trace'),ADAPTERS[name].suite.inspect_native(inner[0])))


def compare(block,domain):
    name,inner=domain
    return ADAPTERS[name].compare(block,inner)
