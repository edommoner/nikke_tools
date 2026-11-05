"""Retain all old141 indices; append original Rei skills and malformed inputs."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('skill_retention_new',ROOT/'research/verify-destructible-skill-rosters-short.py');new=importlib.util.module_from_spec(s);s.loader.exec_module(new)
old=new.prior.prior;suite=new.suite;cross=new.cross

def prepare():
    rows=old.prepare()[0]+new.prepare()[0];packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):return new.native_reference(domain) if domain[0].get('skill_shield_interception_v1') else old.native_reference(domain)
def compare(block,domain):return new.compare(block,domain) if domain[0].get('skill_shield_interception_v1') else old.compare(block,domain)
def validate_rejection(block,name):return new.validate_rejection(block,name) if name.startswith('reject/destructible-skill-rosters/') else old.validate_rejection(block,name)
