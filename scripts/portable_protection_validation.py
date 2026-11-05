"""Malformed protection programs are rejected by the same CUDA/Metal kernel."""
from portable_specs import LIMITS as L,FIELDS as F

def rejection_programs(cases,compile_case):
 import copy
 by={c['name']:c for c in cases};shield=by['protection-shield_from_max_hp_pct-pierce-False-cover-0'];decoy=by['protection-decoy-pierce-False-cover-0'];meta=L['PROTECTION_META_BASE'];definition=L['PROTECTION_DEFINITION_BASE'];base=L['DEFINITION_BASE'];amp=by['protection-amp-multiple-and-partial'];rows=[];expected=[]
 mutations=[('missing-header',shield,meta,0),('header-bits',shield,meta,2),('reserved-header',shield,meta+7,1),('missing-kind',shield,definition,0),('unknown-kind',shield,definition,8),('reserved-kind-bits',shield,definition,513),('end-on-decoy',decoy,definition,258),('shield-wrong-scalar',shield,base+F['STAT'],0),('shield-wrong-kind',shield,base+F['KIND'],4),('nonfinite-capacity',shield,base+F['VALUE']+1,0x7ff00000),('nan-capacity',shield,base+F['VALUE']+1,0x7ff80000),('enemy-resource',shield,L['HEALTH_DEFINITION_BASE']+3,1),('recipient-selector',shield,L['RECIPIENT_BASE'],99),('conflicting-quantity-flags',shield,L['DEFINITION_EXTRA_BASE']+3,4),('conflicting-marker-flags',amp,base+F['FLAGS'],8)]
 hit=next(i for i,c in enumerate(shield['script']) if c[1]==31);command=L['COMMAND_BASE']+hit*8;incoming=L['INCOMING_BASE']+hit*L['INCOMING_WORDS']
 mutations += [('hit-pierce',shield,command+3,2),('hit-cover-mask',shield,command+4,32),('hit-empty-targets',shield,command+5,0),('hit-target-mask',shield,command+5,32),('hit-reserved-payload',shield,command+7,1),('hit-nan-attack',shield,incoming+1,0x7ff80000),('hit-negative-attack',shield,incoming+1,0xbff00000),('hit-inf-coefficient',shield,incoming+3,0x7ff00000),('hit-negative-coefficient',shield,incoming+3,0xbff00000),('hit-attack-range',shield,incoming+1,0x46500000),('hit-coefficient-range',shield,incoming+3,0x42000000)]
 for name,c,at,value in mutations:
  words,metadata=compile_case(c);words[at]=value;rows.append((words,metadata));expected.append(dict(name='wire-protection-'+name,status=64))
 overflow=copy.deepcopy(shield);overflow['effects'][0]['fixed_value']=1e308;rows.append(compile_case(overflow));expected.append(dict(name='protection-capacity-arithmetic-overflow',status=16))
 return rows,expected
