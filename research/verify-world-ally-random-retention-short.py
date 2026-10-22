"""One batch of every previously sealed1234 input; unchanged nested comparators."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=('undying-predicate-retention','undying-predicate','undying-predicate-rosters')
FILES=FAMILIES
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
adapters={name:module('ally_random_retention_'+str(i),'research/verify-world-'+file+'-short.py') for i,(name,file) in enumerate(zip(FAMILIES,FILES))}
prior=adapters[FAMILIES[0]];suite,cross=prior.suite,prior.cross
combine=prior.combine
def prepare():return combine(adapters)
def native_reference(domain):
    name,inner=domain;adapter=adapters[name]
    if hasattr(adapter,'native_reference'):return adapter.native_reference(inner)
    return dict(zip(('battle','skill_trace'),adapter.suite.inspect_native(inner[0])))
def compare(block,domain):
    name,inner=domain;return adapters[name].compare(block,inner)
def validate_rejection(block,name):
    family,label=name.split('/',1);adapter=adapters[family]
    if not hasattr(adapter,'validate_rejection'):raise ValueError('Missing raw rejection contract')
    adapter.validate_rejection(block,label)
