"""Literal shared HP-derived attack inputs and independent arithmetic expectations."""
import itertools,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def buff(name,stat,value,target='all_allies',duration=-1,timing='battle_start',conditions=None):
 return dict(name=name,source='스킬1',type='buff',stat=stat,fixed_value=value,target=target,duration=duration,trigger=dict(timing=[timing],condition=conditions or []))
def packet():return dict(name='measure',source='스킬2',type='damage',stat='damage',fixed_value=100,target='boss',trigger=dict(timing=['hit_count'],condition=[]))
def base(owner,name,effects,owners):
 return dict(name=name,hp_attack_reference=True,effects=effects+[packet() for _ in range(5)],owners=owners+list(range(5)),base_atk=[1000]*5,environment=dict(allies=[dict(base_hp=10000+2000*i,hp=10000+2000*i,base_defense=0) for i in range(5)]),combat=dict(weapons=[dict(enabled=False) for _ in range(5)],targets=[dict(hp=1e12,defense=0)]),script=[],expected_queries=[])
def measure(c,t,totals,flats,percent=None):
 percent=percent or [0]*5
 attacks=c.get('base_atk',[1000]*5)
 for who in range(5):
  c['script'].append([t,0,8,who,0,-1,0,0]);totals[who]+=max(1,round((attacks[who]*(1+percent[who]/100)+flats[who])*1.075))
 q=len(c['expected_queries']);c['script'].append([t,2,0,0,0,q,0,0]);c['expected_queries'].append(dict(damage=totals.copy(),attack_buffs=percent.copy()))
def main():
 cases=[]
 for owner in range(5):
  for target in ('self','all_allies'):
   for pct in (-5,0,12.5):
    for duration in (-1,2):
     c=base(owner,f'hp-attack-basic-{owner}-{target}-{pct}-{duration}',[buff('hp-attack','atk_from_hp_pct',pct,target,duration),buff('hp-up','max_hp_pct',50,duration=.5,timing='on_attack')],[owner,owner]);c['script']=[[0,4,0,0,0,-1,0,0]];totals=[0]*5
     for t,m in [(0,1),(.2,1.5),(.7,1),(2,1)]:
      if t==.2:c['script'].append([t,0,7,owner,0,-1,0,0])
      active=t<2 or duration==-1
      flat=[(10000+2000*i)*m*(pct/100) if active and (target=='all_allies' or i==owner) else 0 for i in range(5)]
      measure(c,t,totals,flat)
     cases.append(c)
 for owner in range(5):
  for order in itertools.permutations(('hp-positive','hp-negative','caster')):
   specs={'hp-positive':('atk_from_hp_pct',1e14),'hp-negative':('atk_from_hp_pct',-1e14),'caster':('atk_caster_based_pct',.1)}
   c=base(owner,f'hp-attack-order-{owner}-'+','.join(order),[buff(k,*specs[k]) for k in order],[owner]*3)
   c['environment']['allies']=[dict(base_hp=10000,hp=10000,base_defense=0) for _ in range(5)]
   c['script']=[[0,4,0,0,0,-1,0,0]];measure(c,0,[0]*5,[1]*5);cases.append(c)
 # HP source conditions are not rechecked by the native attack conversion.
 for owner in range(5):
  for hp_stat in ('max_hp_pct','max_hp_only_pct','hp_caster_based_pct','hp_only_caster_based_pct'):
   c=base(owner,f'hp-attack-native-hp-condition-{owner}-{hp_stat}',[buff('hp-attack','atk_from_hp_pct',10),buff('conditional-hp',hp_stat,20,conditions=['not_self_state:released']),buff('released','',0,target='self',timing='on_attack')],[owner,owner,owner]);c['script']=[[0,4,0,0,0,-1,0,0]];totals=[0]*5
   flat=[((10000+2000*i)*1.2 if hp_stat.startswith('max_hp') else 10000+2000*i+(10000+2000*owner)*.2)*.1 for i in range(5)]
   measure(c,0,totals,flat);c['script'].append([1,0,7,owner,0,-1,0,0]);measure(c,1,totals,flat);cases.append(c)
 for owner in range(5):
  for duration in (-1,2):
   for with_caster in (False,True):
    effects=[buff('hp-ranked','atk_from_hp_pct',5,'allies_top_atk:1',duration),buff('change-ranking','atk_pct',1000,'self',timing='on_attack')];owners=[owner,owner]
    if with_caster:effects.append(buff('caster-ranked','atk_caster_based_pct',10,'allies_top_atk:1',duration));owners.append(owner)
    c=base(owner,f'hp-attack-fresh-rank-{owner}-{duration}-{with_caster}',effects,owners);c['base_atk']=[1000*(i+1) for i in range(5)];c['script']=[[0,4,0,0,0,-1,0,0]];totals=[0]*5
    for t,selected in [(0,4),(1,owner),(2,owner)]:
     percent=[0]*5
     if t:percent[owner]=1000
     if t==1:c['script'].append([1,0,7,owner,0,-1,0,0])
     flat=[0]*5
     if t<2 or duration==-1:flat[selected]=(10000+2000*selected)*.05+(c['base_atk'][owner]*.1 if with_caster else 0)
     measure(c,t,totals,flat,percent)
    cases.append(c)
 for owner in range(5):
  for hp_stat in ('max_hp_only_pct','hp_caster_based_pct','hp_only_caster_based_pct','max_hp_from_max_hp_pct'):
   c=base(owner,f'hp-attack-source-{owner}-{hp_stat}',[buff('hp-attack','atk_from_hp_pct',12.5),buff('hp-source',hp_stat,20,duration=.5,timing='on_attack')],[owner,owner]);c['script']=[[0,4,0,0,0,-1,0,0]];totals=[0]*5
   for t in (0,.2,.7):
    if t==.2:c['script'].append([t,0,7,owner,0,-1,0,0])
    maximum=[(10000+2000*i)*(1.2 if hp_stat=='max_hp_only_pct' and t==.2 else 1)+((10000+2000*owner)*.2 if hp_stat!='max_hp_only_pct' and t==.2 else 0) for i in range(5)]
    measure(c,t,totals,[h*.125 for h in maximum])
   cases.append(c)
 for owner in range(5):
  for duration in (-1,2):
   e=buff('conditional-conversion','atk_from_hp_pct',10,duration=duration,conditions=['not_self_state:released'])
   c=base(owner,f'hp-attack-own-condition-{owner}-{duration}',[e,buff('released','',0,'self',timing='on_attack')],[owner,owner]);c['script']=[[0,4,0,0,0,-1,0,0]];totals=[0]*5
   measure(c,0,totals,[(10000+2000*i)*.1 for i in range(5)]);c['script'].append([1,0,7,owner,0,-1,0,0]);measure(c,1,totals,[(10000+2000*i)*.1 if duration==2 else 0 for i in range(5)]);cases.append(c)
 for owner in range(5):
  for duration in (-1,.5):
   e=buff('stacked-hp-attack','atk_from_hp_pct',5,duration=duration,timing='on_attack');e['max_stack']=3
   c=base(owner,f'hp-attack-stacks-{owner}-{duration}',[e],[owner]);c['script']=[[0,4,0,0,0,-1,0,0]];totals=[0]*5
   for t,stack in [(0,1),(.25,2),(.5,3),(.75,3),(1.25,3 if duration==-1 else 0)]:
    if t<1:c['script'].append([t,0,7,owner,0,-1,0,0])
    measure(c,t,totals,[(10000+2000*i)*.05*stack for i in range(5)])
   cases.append(c)
  removal=dict(name='remove-hp-attack',source='스킬1',type='instant',stat='remove_named_buff',fixed_value=0,target='self',target_effect='hp-attack',trigger=dict(timing=['on_attack'],condition=[]))
  c=base(owner,f'hp-attack-removal-{owner}',[buff('hp-attack','atk_from_hp_pct',10),removal],[owner,owner]);c['script']=[[0,4,0,0,0,-1,0,0]];totals=[0]*5
  measure(c,0,totals,[(10000+2000*i)*.1 for i in range(5)]);c['script'].append([1,0,7,owner,0,-1,0,0]);measure(c,1,totals,[0]*5);cases.append(c)
  for duration in (-1,2):
   ref=buff('Reference','',0,'self');ref['max_stack']=4;ref['trigger']['timing']=['battle_start','on_attack']
   e=buff('hp-attack','atk_from_hp_pct',10,duration=duration);e.update(scaling='stack_count',scaling_ref='Reference')
   c=base(owner,f'hp-attack-reference-{owner}-{duration}',[ref,e],[owner,owner]);c['script']=[[0,4,0,0,0,-1,0,0]];totals=[0]*5
   measure(c,0,totals,[(10000+2000*i)*.1 for i in range(5)]);c['script'].append([1,0,7,owner,0,-1,0,0]);measure(c,1,totals,[(10000+2000*i)*(.2 if duration==-1 else .1) for i in range(5)]);cases.append(c)
 (ROOT/'tests/fixtures/portable-hp-attack.json').write_text(json.dumps(dict(cases=cases),ensure_ascii=False,indent=2)+'\n');print(len(cases),'HP-derived attack shared inputs')
if __name__=='__main__':main()
