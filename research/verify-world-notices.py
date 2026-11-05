"""Shared world notice ordering, multiplicity, termination and raw rejection."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
spec=importlib.util.spec_from_file_location('frame',ROOT/'research/verify-world-frame.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
from calculator.boss_pattern import BOSS_EVENTS

def fixtures():
 base=copy.deepcopy(f.fixtures()[0]);base['duration']=.1;base['patterns'][0]['spec']['hits']=1;rows=[]
 for event in BOSS_EVENTS:
  c=copy.deepcopy(base);c['name']='later-node-notice-before-attack-'+event;c['effects']=[f.effect('invincible',target='all_allies',trigger=dict(timing=[event],condition=[]))];c['owners']=[0];c['patterns'].append(dict(id='b',kind='idle',emit=[event]));rows.append(c)
 for name,events in [('all-four-open-close',list(BOSS_EVENTS)),('duplicate-order',['event:target_spawn','event:part_destroy','event:target_spawn']),('maximum-eight',['event:target_spawn']*8)]:
  c=copy.deepcopy(base);c['name']=name;c['patterns'][0].update(emit=events,emit_end=list(reversed(events)),until=dict(time=.05));c['effects']=[f.effect('def_pct',10,target='all_allies',max_stack=32,trigger=dict(timing=list(BOSS_EVENTS),condition=[]))];rows.append(c)
 c=copy.deepcopy(base);c['name']='notice-after-expiry-tick';c['patterns'][0].update(delay=.05,emit=['event:part_destroy']);c['effects']=[f.effect('crit_dmg',1,name='temp',duration=.05),f.effect('invincible',target='all_allies',trigger=dict(timing=['event:part_destroy'],condition=['not_self_state:temp']))];c['owners']=[0,0];rows.append(c)
 c=copy.deepcopy(base);c['name']='notice-after-battle-start';c['patterns'][0]['emit']=['event:part_destroy'];c['effects']=[f.effect('invincible',target='all_allies',trigger=dict(timing=['event:part_destroy'],condition=['self_state:ready'])),f.effect('crit_dmg',1,name='ready')];c['owners']=[0,0];rows.append(c)
 c=copy.deepcopy(rows[0]);c['name']='close-notice-before-following-attack';c['patterns']=[dict(id='wait',kind='idle',until=dict(time=.05),emit_end=['event:part_destroy']),dict(c['patterns'][0],after=['wait'])];rows.append(c)
 c=copy.deepcopy(base);c['name']='finish-does-not-emit-end';c['patterns'][0]['emit_end']=list(BOSS_EVENTS);c['effects']=[f.effect('def_pct',100,target='all_allies',trigger=dict(timing=list(BOSS_EVENTS),condition=[]))];rows.append(c)
 c=copy.deepcopy(base);c['name']='spawn-notice-does-not-match-other-named-event';c['patterns'][0]['emit']=['event:target_spawn'];c['effects']=[f.effect('def_pct',100,target='all_allies',trigger=dict(timing=['event:unrelated'],condition=[]))];rows.append(c)
 c=copy.deepcopy(base);c['name']='sub-epsilon-notice-once';c['patterns'][0].update(until=dict(time=5e-10),emit=['event:target_spawn'],emit_end=['event:part_destroy']);c['effects']=[f.effect('def_pct',10,target='all_allies',max_stack=32,trigger=dict(timing=list(BOSS_EVENTS),condition=[]))];rows.append(c)
 c=copy.deepcopy(rows[-1]);c['name']='sub-epsilon-repeat-notice-once';c['patterns'][0].update(after=['start','a'],repeat=0);rows.append(c)
 return rows

def negative_inputs():
 base=copy.deepcopy(fixtures()[0]);words,_=f.compile_case(base);d=f.WF_INPUT+16+64;rows=[]
 for name,at,value in [('notice-count9',d+12,9),('notice-id0',d+14,0),('notice-id5',d+14,5),('notice-unused-bits',d+14,1|(1<<3)),('end-count-without-id',d+13,1),('spawn-tag-without-spawn',f.WF_INPUT+8,1),('unused-node-notice',d+2*64+12,1)]:
  w=list(words);w[at]=value;rows.append((name,w))
 base=copy.deepcopy(fixtures()[1]);words,_=f.compile_case(base)
 for name,value in [('spawn-tag-missing',0),('spawn-tag-over-capacity',257)]:
  w=list(words);w[f.WF_INPUT+8]=value;rows.append((name,w))
 return rows
