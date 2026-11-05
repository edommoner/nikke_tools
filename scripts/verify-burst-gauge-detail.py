"""Pending accumulated-gauge GPU port: independent complete-battle oracle.
Reference files supply authored inputs only, never CPU gauge/shot/damage traces.
"""
import copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
spec=importlib.util.spec_from_file_location('burst_gauge_control',ROOT/'scripts/verify-control-detail.py');c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
from detail_coverage import coverage
E=c.E;NAMES=c.NAMES

def scenarios():
 references=json.loads((ROOT/'research/detail-burst-gauge-cpu-references.json').read_text(encoding='utf-8'))
 for case in references['cases']:
  body=copy.deepcopy(case['input']);body['burst_gauge_mode']=case['config_override']['burst_gauge_mode']
  yield case['name'],case['authored_effects'],None,None,body
 references=json.loads((ROOT/'research/detail-burst-gauge-boundary-references.json').read_text(encoding='utf-8'))
 for case in references['cases']:
  body=c.body_for(NAMES,30,True);body['burst_gauge_mode']=case['mode']
  yield 'boundary-'+case['mode']+'-'+case['timing'],case['authored_effects'],None,None,body
 for camera in ('',NAMES[2]):
  body=c.body_for(NAMES,30,True);body['burst_gauge_mode']='accumulate'
  yield 'charge-camera-'+str(bool(camera)),{},None,camera,body
 body=c.body_for(NAMES,30,True);body['burst_gauge_mode']='accumulate'
 mode={'source':'스킬3','name':'gauge weapon mode','type':'weapon_change','target':'self','weapon_type':'SMG','max_ammo':30,'duration_bullets':30,'damage_coeff':{'10':251},'trigger':{'timing':['burst_cast'],'condition':[]}}
 yield 'charge-to-auto-mode-energy',{NAMES[2]:[mode]},None,None,body
 who='라피 : 레드 후드';names=[who]+NAMES[:4];body=c.body_for(names,30,True);body['burst_gauge_mode']='accumulate'
 yield 'skill-energy-exception',{who:[E('부착형 유탄 4','damage','damage',100,'target',event='on_attack_count:3')]},None,None,body


def verify(d,backend):
 out=[]
 for name,effects,controls,camera,body in scenarios():
  with c.p.custom_effects(effects),c.configured(controls,camera):r=compare(d,name,body,backend)
  out.append(r);print(json.dumps(r,ensure_ascii=True),flush=True)
 old=json.loads((ROOT/'research/detail-coverage-infinite.json').read_text(encoding='utf-8'));was={r['character'] for r in old['results'] if r['supported']}
 pinned=json.loads((ROOT/'research/detail-coverage-burst-gauge.json').read_text(encoding='utf-8'));subjects={r['character'] for r in pinned['results'] if r['supported']} - was
 current=coverage();assert subjects <= {r['character'] for r in current['results'] if r['supported']}
 for entry in current['results']:
  if entry['character'] not in subjects:continue
  who=entry['character'];names=[who]+[n for n in NAMES if n!=who][:4]
  for mode in ('fixed','accumulate'):
   body=c.body_for(names,30,True);body['burst_gauge_mode']=mode;r=compare(d,'real-'+who+'-'+mode,body,backend);out.append(r);print(json.dumps(r,ensure_ascii=True),flush=True)
 return out
