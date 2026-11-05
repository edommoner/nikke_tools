"""Literal conditional HP contract,independent of observed GPU/CPU results."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cases=[]
for owner in range(5):
 for stat in ('hp_caster_based_pct','hp_only_caster_based_pct'):
  for target in ('self','all_allies'):
   effects=[dict(name='conditional-hp',source='스킬1',type='buff',stat=stat,fixed_value=20,target=target,duration=-1,
                 trigger=dict(timing=['battle_start'],condition=['not_self_state:released'])),
            dict(name='released',source='스킬2',type='buff',target='self',duration=-1,trigger=dict(timing=['on_attack'],condition=[]))]
   base=[1000*(i+1) for i in range(5)];grant=base[owner]*.2
   first=[dict(hp=hp+(grant if stat=='hp_caster_based_pct' and (target=='all_allies' or i==owner) else 0),
               max_hp=hp+(grant if target=='all_allies' or i==owner else 0)) for i,hp in enumerate(base)]
   final=[dict(hp=hp,max_hp=hp) for hp in base]
   cases.append(dict(name=f'conditional-hp-{owner}-{stat}-{target}',effects=effects,owners=[owner,owner],
       script=[[0,0,0,owner,0,-1,0,0],[0,2,0,0,0,0,0,0],[1,0,7,owner,0,-1,0,0],[1,2,0,0,0,1,0,0]],
       environment=dict(allies=[dict(base_hp=hp,hp=hp,base_defense=0) for hp in base]),
       expected_queries=[dict(allies=first),dict(allies=final)],
       expected_native_queries=[dict(allies=first),dict(allies=first)]))
assert len(cases)==20
(ROOT/'tests/fixtures/portable-health-runtime.json').write_text(json.dumps(dict(cases=cases),ensure_ascii=False,indent=2)+'\n')
