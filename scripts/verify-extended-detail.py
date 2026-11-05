"""Coverage expansion evidence: independently simulated complete real squads.
No CPU burst times, shot times, selected targets or buff states feed CUDA.
"""
import copy,json,sys,time,hashlib,math
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'));sys.path.insert(0,str(ROOT/'app'))
from detail_coverage import body_for,coverage,a

def scenarios(include_coverage=True):
 out=[]
 if include_coverage:
  for r in coverage()['results']:
   if r['supported']:
    names=[r['character']]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=r['character']][:4]
    out.append(('coverage:'+r['character'],body_for(names,60)))
 names=['리타','마스트 : 로망틱 메이드','앨리스','모더니아','N102']
 out.append(('liter-alice-owned-180',body_for(names,180,True)))
 b=body_for(['N102','도라','앨리스','모더니아','얀'],180);out.append(('rank-refresh-alice-burst-180',b))
 b=body_for(['마스트 : 로망틱 메이드','루주','앨리스','도라','모더니아'],180,True);b['burst_policy']='mast3';b['stat_deltas']={'루주':{'hp':9000000}};b['profile']['chars']['앨리스']['cube']={'name':'렐릭 피어싱 큐브','level':7};out.append(('hp-threshold-lifesteal-pierce-mast3-180',b))
 b=body_for(['미하라','리타','마스트 : 로망틱 메이드','앨리스','모더니아'],180);out.append(('mihara-deferred-b3-and-last-bullet-180',b))
 b=body_for(['히메노','미란다','앨리스','모더니아','루드밀라'],180,True);b['enemy']['core_px']=0;b['enemy']['code']='작열';out.append(('sr-targets-exclude-caster-enemy-defense-180',b))
 for lv in (1,7,10):
  b=body_for(['리타','크라운','앨리스','모더니아','N102'],180,True)
  b['profile']['chars']['크라운']['skill_levels']={'1':lv,'2':lv,'3':lv}
  out.append((f'crown-stack-heal-shield-lv{lv}-180',b))
 b=body_for(['루주','크라운','앨리스','마스트 : 로망틱 메이드','모더니아'],180,True)
 b['burst_policy']='mast3'
 b['profile']['chars']['앨리스']['cube']={'name':'렐릭 베어 큐브','level':7}
 b['patches']={'크라운':{'skill_levels':{'1':10,'2':10}},'앨리스':{'equip_skills':{'charge_speed_pct':[4.3,4.3,6.2]}}}
 b['stat_deltas']={'크라운':{'hp':500000},'앨리스':{'atk':12345}}
 out.append(('crown-charge-cover-auto-reload-owned-180',b))
 b=body_for(['리타','키리','크라운','루드밀라','크로우'],60,True)
 out.append(('kiri-two-of-three-defenders-owned-60',b))
 return out
