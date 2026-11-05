from detail_gpu import weapon_rows,UnsupportedDetail
"""Full-squad CPU/GPU checks for list burst priorities and owned charge weapons."""
import copy,hashlib,json,sys,time
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for

def scenarios():
 names=['리타','도라','앨리스','모더니아','얀']
 for label,patterns in [('list-priority',{'앨리스':[1,3],'모더니아':[2,4]}),('empty-list-is-low-priority',{'리타':[],'얀':[1,3]}),('both-empty-still-cast',{'앨리스':[],'모더니아':[]})]:
  b=body_for(names,60,True)
  b['patches']={'앨리스':{'skill_levels':{'1':9,'2':8,'3':10},'equip_skills':{'charge_speed_pct':[4.3,4.3,6.2],'max_ammo_pct':[11.12,11.12,12.34]}}}
  b['stat_deltas']={'앨리스':{'atk':12345,'hp':54321,'def':321}}
  yield label,b,patterns
 b=body_for(['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'],60,True)
 yield 'list-fallback-after-early-cycles',b,{'마스트 : 로망틱 메이드':[1],'도라':[2]}
 b=body_for(['리타','도라','앨리스','모더니아','얀'],30,True);b['burst_policy']='mast3'
 yield 'mast-absent-charge-equipment',b,{}
