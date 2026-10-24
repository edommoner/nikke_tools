"""Preserve old31 indices and append the fixed-quantity accumulation18 inputs."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
def adapter(name):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=adapter('verify-destructible-body-lifesteal-retention-short');new=adapter('verify-destructible-body-accum-short');suite,cross=new.suite,new.cross
def prepare():
    rows=old.prepare()[0]+new.prepare()[0];packed=array.array('I',[len(rows)])
    for _,words,_ in rows:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):return new.native_reference(domain) if domain[0].get('body_accumulation_v1') else old.native_reference(domain)
def compare(block,domain):return new.compare(block,domain) if domain[0].get('body_accumulation_v1') else old.compare(block,domain)
def validate_rejection(block,name):return new.validate_rejection(block,name) if name.startswith('reject/destructible-body-accum/') else old.validate_rejection(block,name)
