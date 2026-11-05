"""Retain all prior 759 cases and append entry-reload native/diagnostic cases."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
prior=module('entry_reload_prior_regression','research/verify-world-regression-short.py')
entry=module('entry_reload_regression_addition','research/verify-world-entry-reload-short.py')
adapters=dict(prior.ADAPTERS,**{'entry-reload':entry})
suite,cross=prior.suite,prior.cross

def prepare():return prior.combine(adapters)
def native_reference(domain):
    name,inner=domain;adapter=adapters[name]
    if hasattr(adapter,'native_reference'):return adapter.native_reference(inner)
    return dict(zip(('battle','skill_trace'),adapter.suite.inspect_native(inner[0])))
def compare(block,domain):
    name,inner=domain;return adapters[name].compare(block,inner)
def validate_rejection(block,name):
    family,label=name.split('/',1);adapter=adapters[family]
    if hasattr(adapter,'validate_rejection'):adapter.validate_rejection(block,label)
