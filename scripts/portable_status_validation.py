"""Status wire validation is exercised identically by CUDA and Metal."""
from portable_specs import LIMITS as L,FIELDS as F

def rejection_programs(cases,compile_case):
 by={c['name']:c for c in cases};count=by['status-application-debuff_immune_count'];named=by['status-application-debuff_immune:harm'];cleanse=by['status-cleanse-limit-None-self'];enemy=by['status-enemy-generation-debuff_immune']
 base=L['DEFINITION_BASE'];stride=L['DEFINITION_WORDS'];meta=L['STATUS_META_BASE'];rows=[];expected=[]
 mutations=[('header-missing',count,meta,0),('header-overflow',count,meta,8),('metadata-reserved',count,meta+7,1),('count-absent-value-with-nonzero-scalar',count,base+F['FLAGS'],48),('immunity-on-scalar',count,base+stride+F['FLAGS'],16),('value-flag-on-global',named,base+F['FLAGS'],96),('named-negative-reference',named,base+F['TARGET_NAME'],0xffffffff),('named-reference-overflow',named,base+F['TARGET_NAME'],256),('global-reference-not-absent',enemy,base+F['TARGET_NAME'],0),('pool-name-overflow',count,base+F['NAME'],256),('nan-charge-base',count,base+F['VALUE']+1,0x7ff80000),('inf-charge-base',count,base+F['VALUE']+1,0x7ff00000),('cleanse-policy-zero',cleanse,base+5*stride+F['TARGET'],0),('cleanse-policy-overflow',cleanse,base+5*stride+F['TARGET'],3),('cleanse-infinite-limit',cleanse,base+5*stride+F['VALUE']+1,0x7ff00000),('cleanse-nan-limit',cleanse,base+5*stride+F['VALUE']+1,0x7ff80000),('cleanse-recipient-flags',cleanse,L['RECIPIENT_BASE']+5*8+7,1),('cleanse-enemy-payload-on-ally',cleanse,L['DAMAGE_DEFINITION_BASE']+5*L['DAMAGE_DEFINITION_WORDS'],1)]
 for name,c,field,value in mutations:
  words,metadata=compile_case(c);words[field]=value;rows.append((words,metadata));expected.append(dict(name='wire-status-'+name,status=64))
 return rows,expected
