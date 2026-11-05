"""Beyond-command-count scheduling, MT rollover and fail-closed dynamic traces."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_backend import execute,source_hashes
spec=importlib.util.spec_from_file_location('world_frame',ROOT/'research/verify-world-frame.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def fixtures():
 base=copy.deepcopy(f.fixtures()[0]);base['patterns'][0]['spec'].update(atk=1,target='random:3',hits=72,interval=1/60);base['duration']=1.3;base['name']='beyond64-72-attacks';rows=[base]
 c=copy.deepcopy(base);c['name']='same-frame-512-random3-mt-rollover';c['duration']=.05;c['patterns'][0]['spec'].update(hits=512,interval=0);rows.append(c)
 for name,target,hits,queries,records in [('target-query-capacity','slot:1',1025,1024,1024),('recipient-trace-capacity','all',411,410,2048)]:
  c=copy.deepcopy(base);c['name']=name;c['duration']=.05;c['effects']=[f.effect('invincible',target='all_allies')];c['owners']=[0];c['patterns'][0]['spec'].update(target=target,hits=hits,interval=0);c.update(expected_status=2,expected_queries=queries,expected_records=records);rows.append(c)
 c=copy.deepcopy(f.fixtures()[0]);c['name']='expiry-end-notice-before-target-selection';c['patterns'][0]['delay']=.2;c['patterns'][0]['spec'].update(target='top_atk:1',hits=1);c['effects']=[f.effect('crit_dmg',name='temp',duration=.1),f.effect('atk_pct',1000,trigger=dict(timing=['event:state_end:temp'],condition=[]))];c['owners']=[0,0];rows.append(c)
 return rows
