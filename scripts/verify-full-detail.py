"""End-to-end differential checks: complete real squads and owned growth adapter.
GPU independently chooses all burst and shot times. No CPU event replay.
"""
import copy,json,sys,hashlib,time
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
import engine_worker as adapter

def fixture(duration=180,policy='auto',grown=False,reverse=False):
 names=['모더니아','루주','마스트 : 로망틱 메이드','도라','얀']
 if reverse:names=['얀','도라','루주','모더니아','마스트 : 로망틱 메이드']
 chars={n:{k:copy.deepcopy(v) for k,v in adapter.spec.DEFAULT_CHAR.items() if k in adapter.spec.GROWTH_KEYS} for n in names}
 cube_names=[n for n,data in adapter.spec.CUBES.items() if data['stat'] in ('accuracy_pct','charge_speed_pct','reload_speed_pct','max_ammo_pct')]
 for i,(n,c) in enumerate(chars.items()):
  c['cube']={'name':cube_names[i%len(cube_names)] if grown else '__none__','level':1+i*3 if grown else 1}
  c['favorite_stage']=0;c['collection_stage']='SR15' if grown else '없음'
  if grown:
   c['breakthrough']=i%4;c['core_enhancement']=4 if i%4==3 else 0;c['affinity']=1+i*7
   c['skill_levels']={'1':1+i*2,'2':10-i,'3':3+i}
   for gear in c['equipment'].values():gear['level']=i%6
 return {'profile':{'chars':chars,'_account':{'console':adapter.spec.DEFAULT_CHAR['console']}},'squad':names,'duration':duration,'level':400,'enemy':{'def':31784,'code':'풍압','core_px':0 if reverse else 50,'distance':25},'burst_policy':policy,'patches':{'루주':{'skill_levels':{'1':8},'equip_skills':{'max_ammo_pct':71.12,'charge_speed_pct':12.34}}} if grown else {},'stat_deltas':{'마스트 : 로망틱 메이드':{'atk':12345,'hp':100000,'def':345}} if grown else {}}
