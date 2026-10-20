"""Authored input corpus;no CPU battle states or firing times in GPU inputs."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def make(owner,base_mode,mode,delay,scenario):
 def eff(name,kind,stat,target,timing,**kw):return dict(name=name,source='스킬1',type=kind,stat=stat,target=target,trigger=dict(timing=[timing],condition=[]),**kw)
 no_crit=eff('no-critical','buff','crit_rate','all_allies','battle_start',fixed_value=-15,duration=-1)
 ready=eff('Ready','buff','','self','battle_start',duration=-1 if scenario in ('refresh','reenter') else .2)
 a=dict(name='Mode A',source='스킬1',type='weapon_change',weapon_type='SR' if mode=='charge' else 'AR',damage_coeff=200,max_ammo=5,fire_rate=10,fire_rate_max=10,charge=mode=='charge',charge_time=.2,full_charge_mult=100,pellets=1,muzzles=1,post_fire_delay=0,burst_energy=0,core_dmg_mult=200,reload_time=.5,duration=-1,duration_bullets=2,target='self',trigger=dict(timing=['on_attack' if scenario=='shot-enters' else 'passive' if scenario=='passive-false' else 'battle_start'],condition=['self_state:Never' if scenario=='passive-false' else 'self_state:Ready']))
 if scenario in ('refresh','reenter'):a['trigger']['timing'].append('event:full_reload')
 if scenario=='finite':a['duration']=.15
 effects=[no_crit,ready,a];owners=[owner]*3;delays={'Mode A':delay}
 if scenario in ('remove','reenter'):
  effects.append(eff('remove-mode','instant','remove_named_buff','self','event:cover_healed',fixed_value=0,target_effect='Mode A'));owners.append(owner)
 if scenario=='replace':
  b=dict(a,name='Mode B',damage_coeff=300,trigger=dict(timing=['event:cover_healed'],condition=[]));effects.append(b);owners.append(owner);delays['Mode B']=.17
 w=dict(enabled=True,base_weapon_type='SR' if base_mode=='charge' else 'AR',mode=base_mode,capacity=3,coefficient=100,interval=.3,charge=.1,full_charge_mult=100,reload=.5,gauge=0,pellets=1)
 weapons=[dict(enabled=False) for _ in range(5)];weapons[owner]=w
 script=[]
 times=[0,.1,.2] if scenario=='short' else [0,.1,.2,.3,.4,.6,1.2]
 for t in times:
  if t==.1 and scenario in ('remove','replace','reenter'):script.extend([[(round(t*60)-1)/60,24,0,0,0,-1,0,0],[t,0,17,owner,0,-1,0,0]])
  if t==.1 and scenario=='refresh' or t==.3 and scenario=='reenter':script.extend([[(round(t*60)-1)/60,24,0,0,0,-1,0,0],[t,0,19,owner,0,-1,0,0]])
  script.extend([[t,24,0,0,0,-1,0,0],[t,2,0,0,0,len([c for c in script if c[1]==2]),0,0]])
 expected=[{} for _ in times]
 if scenario=='shot-enters' and base_mode=='auto':
  damage=[0]*5;damage[owner]=1000;expected[0]={'damage':damage}
 elif scenario!='shot-enters':
  damage=[0]*5
  if delay==0 and mode=='auto':damage[owner]=2000
  expected[0]={'damage':damage}
 return dict(name=f'mode-entry-{owner}-{base_mode}-{mode}-{delay}-{scenario}',mode_entry_reference=True,mode_entry_context=dict(owner=owner,delays=delays,scenario=scenario),effects=effects,owners=owners,combat=dict(weapons=weapons,targets=[dict(hp=1e12,defense=0)]),script=script,expected_queries=expected)
def main():
 cases=[make(o,b,m,d,s) for o in range(5) for b in ('auto','charge') for m in ('auto','charge') for d in (0,.39) for s in ('initial','short','shot-enters','refresh','remove','replace','reenter','finite','passive-false')]
 for o in range(5):
  for b in ('auto','charge'):
   for m in ('auto','charge'):
    for scenario in ('initial','shot-enters'):
     c=make(o,b,m,0,scenario);c['name']=f'mode-entry-{o}-{b}-{m}-absent-{scenario}';c['mode_entry_context']['delays']={};cases.append(c)
 (ROOT/'tests/fixtures/portable-mode-entry.json').write_text(json.dumps(dict(cases=cases),ensure_ascii=False,indent=2)+'\n');print(len(cases),'mode entry inputs authored')
if __name__=='__main__':main()
