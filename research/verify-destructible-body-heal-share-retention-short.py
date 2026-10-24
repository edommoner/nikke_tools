"""Retain all49 old indices and append complete sharing rosters12."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
def adapter(name):
    s=importlib.util.spec_from_file_location(name,Path(__file__).with_name(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
old=adapter('verify-destructible-body-accum-retention-short');new=adapter('verify-destructible-body-heal-share-short');suite,cross=new.suite,new.cross
from portable_destructible_roster_skill_comparison import compare_body_consumers
def prepare():
    rows=old.prepare()[0]+new.prepare()[0];data=array.array('I',[len(rows)])
    for _,w,_ in rows:data.extend(w)
    if sys.byteorder!='little':data.byteswap()
    return rows,data.tobytes()
def native_reference(domain):return new.native_reference(domain) if domain[0].get('body_heal_sharing_v1') else old.native_reference(domain)
def compare(block,domain):return compare_body_consumers(block,domain,native_reference(domain))
def validate_rejection(block,name):return old.validate_rejection(block,name)
