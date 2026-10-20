"""Common CUDA/Metal wire and finite-quantity boundaries for ordered instants."""
import copy
from portable_specs import LIMITS as L,FIELDS as F

def rejection_programs(cases,compile_case):
 case=next(c for c in cases if c['name']=='instant-list-heal-21');base=L['RECIPIENT_BASE'];node=L['RECIPIENT_NODE_BASE'];definition=L['DEFINITION_BASE'];rows=[];expected=[]
 for name,at,value in [('count',base+1,22),('reserved-flags',base+7,8),('recursive-node',node,17),('unknown-kind',definition+F['KIND'],99)]:
  words,meta=compile_case(case);words[at]=value;rows.append((words,meta));expected.append(dict(name='wire-instant-list-'+name,status=32 if name=='unknown-kind' else 64))
 for stat in ('heal_hp_pct','shield_heal_pct'):
  if stat=='shield_heal_pct':selected=copy.deepcopy(next(c for c in cases if c['name']=='instant-list-shield_from_max_hp_pct-heal-None'))
  else:selected=copy.deepcopy(case);selected['effects'][0]['stat']=stat
  selected['effects'][-1]['fixed_value']=1e308;rows.append(compile_case(selected));expected.append(dict(name='instant-list-overflow-'+stat,status=16))
 return rows,expected
