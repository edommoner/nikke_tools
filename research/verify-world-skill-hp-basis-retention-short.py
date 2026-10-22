"""Retain all eight sealed families in one dispatch, using their unchanged oracles."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FAMILIES=('heal-share-regression','parts-skill-world','heal-share-rosters','ally-burst','ally-burst-rosters','mode-capacity','mode-capacity-instant','mode-capacity-rosters')
FILES=('heal-share-regression','parts-skill','heal-share-rosters','ally-burst','ally-burst-rosters','mode-capacity','mode-capacity-instant','mode-capacity-rosters')
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
adapters={name:module('hp_retention_'+str(i),'research/verify-world-'+file+'-short.py') for i,(name,file) in enumerate(zip(FAMILIES,FILES))}
prior=adapters['heal-share-regression'];suite,cross=prior.suite,prior.cross
def prepare():return prior.prior.prior.combine(adapters)
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
