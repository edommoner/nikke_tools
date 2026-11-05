"""Existing4682 full-word preservation and new world-frame raw admission failures."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_backend import execute,source_hashes
OLD_IN=86016;NEW_IN=88848;OLD_OUT=159744;NEW_OUT=225280
sha=lambda b:hashlib.sha256(b).hexdigest()
def negative_inputs():
 s=importlib.util.spec_from_file_location('world_frame_fixture',ROOT/'research/verify-world-frame.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 words,_=m.compile_case(m.fixtures()[0]);rows=[]
 for name,word,value in [('graph-magic',86016,1),('graph-count',86017,33),('manual-frame-count',86018,1),('wrong-clock',86019,2),('finish-disabled',86020,0),('graph-reserved',86021,1),('graph-tail',86031,1),('authored-clear-mask',86016+2064+2,1),('payload-op',88336,31),('payload-time',88337,1),('payload-pierce',88339,2),('cpu-cover-mask',88340,1),('cpu-victim-mask',88341,1),('payload-reserved',88342,1),('bad-victim-rule',88348,4),('all-count',88349,1),('all-slots',88350,1),('all-taunt-flag',88351,1),('unused-payload',88352,1),('rng-disabled',0,0)]:
  v=list(words)
  if name=='rng-disabled':v[m.L['ENEMY_TARGET_META_BASE']]=0
  else:v[word]=value
  rows.append((name,v))
 for name,at,value in [('nan-attack',88344,float('nan')),('negative-attack',88344,-1),('infinite-coefficient',88346,float('inf')),('oversized-coefficient',88346,1000001),('duration-without-final-advance',86022,2)]:
  v=list(words);v[at:at+2]=list(struct.unpack('<II',struct.pack('<d',value)));rows.append((name,v))
 return rows
