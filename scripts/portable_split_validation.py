"""Same split/ordered-union rejection stimuli on both GPU backends."""
from portable_specs import LIMITS as L,FIELDS as F

def rejection_programs(cases,compile_case):
 case=next(c for c in cases if c['name']=="split-target-['self', 'allies_lowest_hp_excl:2']")
 meta=L['RECIPIENT_META_BASE'];plan=L['RECIPIENT_BASE'];node=L['RECIPIENT_NODE_BASE'];definition=L['PROTECTION_DEFINITION_BASE'];base=L['DEFINITION_BASE']
 mutations=[('node-capacity',meta,L['RECIPIENT_NODES']+1),('reserved-meta',meta+7,1),('empty-union',plan+1,0),('wide-union',plan+1,22),('node-range',plan+2,L['RECIPIENT_NODES']),('union-reserved',plan+3,1),('union-lazy-flag',plan+7,16),('recursive-node',node,17),('enemy-node',node,4),('unknown-node',node,22),('node-count',node+1,6),('node-mask',node+2,32),('node-order',node+4,9),('split-missing-policy',definition,0),('split-wrong-stat',base+F['STAT'],45),('split-wrong-kind',base+F['KIND'],4),('split-lifetime-flag',definition,264),('split-missing-feature',L['PROTECTION_META_BASE'],1)]
 rows=[];expected=[]
 for name,at,value in mutations:
  words,metadata=compile_case(case);words[at]=value;rows.append((words,metadata));expected.append(dict(name='wire-split-'+name,status=64))
 return rows,expected
