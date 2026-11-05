"""Retain prior95, annotated skills10 and B1-presence20 through one combiner."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name):
    s=importlib.util.spec_from_file_location('burst1_retention_'+name,ROOT/'research'/('verify-world-'+name+'-short.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
adapters={name:load(name) for name in ('below-def-retention','skill-weapon','burst1-ally')};prior=adapters['below-def-retention']
suite,cross,combine=prior.suite,prior.cross,prior.combine

def prepare():return combine(adapters)
def native_reference(domain):return adapters[domain[0]].native_reference(domain[1])
def compare(block,domain):return adapters[domain[0]].compare(block,domain[1])
def validate_rejection(block,name):
    tag,label=name.split('/',1);adapters[tag].validate_rejection(block,label)
