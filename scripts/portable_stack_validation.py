"""Forged-wire and bounded-domain failures, identical for CUDA and Metal."""
import copy
from portable_specs import LIMITS as L,FIELDS as F

def rejection_programs(cases,compile_case):
    by_name={c['name']:c for c in cases};programs=[];expected=[]
    own=by_name['stack-buff_stack_add-named-0.0'];init=by_name['stack-init-first-registered-definition'];enemy=by_name['stack-dot-zero-and-refresh-1'];reference=by_name['stack-debuff-delta-reference-0.0-resource']
    base=L['DEFINITION_BASE'];width=L['DEFINITION_WORDS'];meta=L['MODE_BASE'];mw=L['MODE_WORDS']
    for name,c,field,value in [
        ('metadata-tag',own,meta,0),('metadata-native-kind',own,meta+1,0),('metadata-nan-duration',own,meta+3,0x7ff80000),
        ('metadata-runtime-flag-range',own,meta+5,2),('metadata-runtime-policy-missing',by_name['stack-birth-runtime-policy-init-True-refresh-False'],meta+mw+5,0),('metadata-runtime-with-finite-duration',own,meta+5,1),('metadata-runtime-on-instant',own,meta+mw+5,1),
        ('metadata-padding',own,meta+31,1),('instant-native-kind',own,meta+mw+1,1),
        ('init-not-first-definition',init,meta+2*mw+4,2),('init-target-overflow',init,meta+2*mw+4,257),
        ('policy-zero',own,base+width+F['TARGET'],0),('policy-overflow',own,base+width+F['TARGET'],3),
        ('delta-nan',own,base+width+F['VALUE']+1,0x7ff80000),('delta-inf',own,base+width+F['VALUE']+1,0x7ff00000),
        ('target-name-overflow',own,base+width+F['TARGET_NAME'],256),('recipient-flags',own,L['RECIPIENT_BASE']+8+7,1),
        ('ally-enemy-payload',own,L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS']+1,1),
        ('enemy-route',enemy,L['DAMAGE_DEFINITION_BASE']+2*L['DAMAGE_DEFINITION_WORDS'],10),
        ('enemy-count',enemy,L['DAMAGE_DEFINITION_BASE']+2*L['DAMAGE_DEFINITION_WORDS']+1,0),
        ('enemy-payload',enemy,L['DAMAGE_DEFINITION_BASE']+2*L['DAMAGE_DEFINITION_WORDS']+2,1),
        ('immune-bit-on-scalar',own,base+F['FLAGS'],8),('debuff-gauge-only-mode',reference,L['REFERENCE_DEFINITION_BASE']+2*4,2)]:
        words,metadata=compile_case(c);words[field]=value;programs.append((words,metadata));expected.append(dict(name='wire-stack-'+name,status=64))
    for name,c in [('unlimited-own-overflow',by_name['stack-buff_stack_add-named-1e+308']),('unlimited-max-overflow',by_name['stack-max-raw-integer-1e+308'])]:
        changed=copy.deepcopy(c);changed['effects'][0]['max_stack']=-1
        programs.append(compile_case(changed));expected.append(dict(name='stack-'+name,status=2))
    return programs,expected
