"""Keep the old796 unchanged and append all43 healing contracts/raw10 guards."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
prior=module('heal_regression_prior','research/verify-world-entry-reload-regression-short.py')
addition=module('heal_regression_addition','research/verify-world-heal-share-short.py')
adapters=dict(prior.adapters,**{'heal-share':addition})
suite,cross=prior.suite,prior.cross
def prepare():return prior.prior.combine(adapters)
def native_reference(domain):
    name,inner=domain;adapter=adapters[name]
    if hasattr(adapter,'native_reference'):return adapter.native_reference(inner)
    return dict(zip(('battle','skill_trace'),adapter.suite.inspect_native(inner[0])))
def compare(block,domain):
    name,inner=domain;return adapters[name].compare(block,inner)
def validate_rejection(block,name):
    family,label=name.split('/',1);adapter=adapters[family]
    if hasattr(adapter,'validate_rejection'):adapter.validate_rejection(block,label)
