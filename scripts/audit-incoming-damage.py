"""CPU-only incoming damage/layer references for the next integrated GPU port.

These cases must remain rejected by the current GPU compiler. CPU reference
success is never reported as an incoming-combat GPU implementation.
"""
import copy,dataclasses,hashlib,importlib.util,json,math
from pathlib import Path
from datetime import datetime,timezone
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('incoming_layers',ROOT/'scripts/verify-boss-buffs-detail.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
NAMES=v.v.NAMES;owner=NAMES[0]
def buff(name,stat,value,**kw):return v.E(name,'buff',stat,value,**kw)
cases=[
 ('body',100000,False,[],{}),
 ('defense',100000,False,[buff('defense','def_pct',50)],{'def_pct':50}),
 ('received',100000,False,[buff('reduction','received_dmg_pct',-50)],{'received_pct':-50}),
 ('invincible',100000,False,[buff('invincible','invincible',1)],{}),
 ('shield',10000000,False,[buff('shield','shield_from_max_hp_pct',10)],{}),
 ('shield-pierce',10000000,True,[buff('shield','shield_from_max_hp_pct',10)],{}),
 ('two-shields',10000000,False,[buff('first shield','shield_from_max_hp_pct',10),buff('second shield','shield_from_max_hp_pct',20)],{}),
 ('two-shields-pierce',10000000,True,[buff('first shield','shield_from_max_hp_pct',10),buff('second shield','shield_from_max_hp_pct',20)],{}),
 ('cover',10000000,False,[v.E('reload before hit','instant','force_reload',0)],{}),
 ('cover-pierce',10000000,True,[v.E('reload before hit','instant','force_reload',0)],{}),
 ('cover-disabled',10000000,False,[v.E('reload before hit','instant','force_reload',0),buff('no cover','cover_disabled',1)],{}),
 ('shield-before-cover',10000000,False,[v.E('reload before hit','instant','force_reload',0),buff('shield','shield_from_max_hp_pct',10)],{}),
 ('shield-and-cover-pierce',10000000,True,[v.E('reload before hit','instant','force_reload',0),buff('shield','shield_from_max_hp_pct',10)],{}),
 ('decoy',10000000,False,[buff('decoy','decoy',10)],{}),
 ('decoy-pierce',10000000,True,[buff('decoy','decoy',10)],{}),
 ('shared',100000,False,[buff('split','received_dmg_split_even',1,target='all_allies')],{}),
 ('undying',10000000,False,[buff('undying','undying',1)],{}),
 ('lethal-trigger-undying',10000000,False,[buff('last stand','undying',1,event='event:lethal_hit',max_trigger=1,duration=2)],{}),
 ('down',10000000,False,[],{}),
 ('literal-legacy-reduction',100000,False,[buff('legacy marker','damage_reduction_pct',-50)],{'literal_legacy_marker':True}),
]
rows=[]
for name,atk,pierce,effects,expected in cases:
 b=v.v.body_for(NAMES,1,False);b['seed']=12345
 for c in b['profile']['chars'].values():c.update(equip_skills={k:0 for k in v.a.spec.DEFAULT_CHAR['equip_skills']},collection_stage='없음',favorite_stage=0,cube={'name':'__none__','level':0})
 b['enemy']['patterns']=[dict(id='incoming',kind='attack',delay=.1,until={'time':.2},spec=dict(coeff=100,atk=atk,target='slot:1',pierce=pierce))]
 captured={};events=[];execute=v.a.sim.execute
 from calculator import buff_manager
 notify=buff_manager.BuffManager.notify
 def executed(run):
  result=execute(run);captured['result']=result;return result
 def notified(self,event,t,caster,**context):
  if event in ('received_hit','event:cover_hit','event:lethal_hit','event:self_down'):events.append(dict(event=event,time=t,caster=caster))
  return notify(self,event,t,caster,**context)
 with v.v.t.p.custom_effects({owner:effects}),patch.object(v.a.sim,'execute',executed),patch.object(buff_manager.BuffManager,'notify',notified):cpu=v.a.evaluate(b)
 hits=[dataclasses.asdict(h) for h in captured['result'].squad_hits]
 assert hits,name
 base=cpu['base_stats'][owner];damage=max((atk-base['def']*(1+expected.get('def_pct',0)/100))*max(0,1+expected.get('received_pct',0)/100),1)
 first_expected=damage/5 if name=='shared' else damage
 assert math.isclose(hits[0]['damage'],first_expected,rel_tol=1e-12,abs_tol=1e-8),(name,hits[0]['damage'],first_expected)
 if name in ('shield','two-shields'):assert hits[0]['shield']>0 and hits[0]['hp']==0
 if name in ('shield-pierce','two-shields-pierce'):assert hits[0]['shield']>0 and hits[0]['hp']>0
 if name=='cover':assert hits[0]['cover']>0 and hits[0]['hp']==0 and any(e['event']=='event:cover_hit' for e in events)
 if name=='cover-pierce':assert hits[0]['cover']>0 and hits[0]['hp']>0
 if name=='cover-disabled':assert hits[0]['cover']==0 and hits[0]['hp']>0
 if name=='shield-before-cover':assert hits[0]['shield']>0 and hits[0]['cover']==0 and hits[0]['hp']==0
 if name=='shield-and-cover-pierce':assert hits[0]['shield']>0 and hits[0]['cover']>0 and hits[0]['hp']>0
 if name.startswith('decoy'):assert hits[0]['decoy']>0 and hits[0]['hp']==0
 if name=='invincible':assert hits[0]['hp']==0 and any(e['event']=='received_hit' for e in events)
 if name=='shared':
  assert len(hits)==5 and all(math.isclose(h['damage'],damage/5,rel_tol=1e-12) for h in hits)
  assert sum(e['event']=='received_hit' for e in events)==1
 if name in ('undying','lethal-trigger-undying'):assert hits[0]['hp_after']==1 and not hits[0]['down']
 if name=='lethal-trigger-undying':assert any(e['event']=='event:lethal_hit' for e in events)
 if name=='down':assert hits[0]['down'] and hits[0]['hp_after']==0 and any(e['event']=='event:self_down' for e in events)
 with v.v.t.p.custom_effects({owner:effects}):
  try:v.a.evaluate({**b,'_compile_gpu_detail':True});accepted=True;issues=[]
  except v.g.UnsupportedDetail as e:accepted=False;issues=e.issues
 assert not accepted,name
 row=dict(name=name,base_stats=base,attack=b['enemy']['patterns'][0]['spec'],hits=hits,events=events,gpu_accepted=False,gpu_issues=issues,cpu_model_note='The literal legacy damage_reduction_pct marker leaves this CPU incoming formula unchanged; no game-correctness claim.' if expected.get('literal_legacy_marker') else '')
 rows.append(row);print(json.dumps(row,ensure_ascii=True),flush=True)
files=['scripts/audit-incoming-damage.py','app/engine_worker.py','app/engine_compat.py','research/upstream/nikke-calc-master/calculator/timeline.py','research/upstream/nikke-calc-master/calculator/buff_manager.py','research/upstream/nikke-calc-master/calculator/boss_pattern.py']
r=dict(generated_at=datetime.now(timezone.utc).isoformat(),cpu_reference_verified=True,gpu_implemented=False,objective_complete=False,cases=rows,source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
(ROOT/'research/detail-incoming-damage-cpu-reference.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
