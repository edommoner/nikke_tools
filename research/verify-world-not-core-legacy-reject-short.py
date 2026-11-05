"""Existing entry must keep rejecting raw non-core condition wire."""
import array,importlib.util
from pathlib import Path
s=importlib.util.spec_from_file_location('legacy_notcore',Path(__file__).with_name('verify-world-not-core-short.py'));base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
suite,cross=base.suite,base.cross
def prepare():
    row=base.prepare()[0][0];w=row[1];return [('reject/not-core-old-entry',w,None)],array.array('I',[1]+list(w)).tobytes()
def native_reference(domain):raise AssertionError('Rejection only')
def compare(block,domain):raise AssertionError('Rejection only')
def validate_rejection(block,name):assert name=='reject/not-core-old-entry' and block[0]==64
