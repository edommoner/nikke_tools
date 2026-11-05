"""Malformed late-pass identities are checked by the shared GPU admission."""
import copy
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import double_words

def rejection_programs(cases,compile_case):
 source,metadata=compile_case(next(c for c in cases if c.get('hp_attack_reference')));d=L['DEFINITION_BASE'];health=L['HEALTH_DEFINITION_BASE'];recipient=L['RECIPIENT_BASE']
 changes=[('legacy-kind',{d+F['KIND']:4}),('damage-kind',{d+F['KIND']:3}),('weapon-kind',{d+F['KIND']:2}),('instant-kind',{d+F['KIND']:1}),('enemy',{health+3:1}),('allied-flag',{health+1:1}),('health-scaling',{health:1}),('mapped-query',{recipient+7:source[recipient+7]|4}),('damage-flags',{d+F['DAMAGE_FLAGS']:1}),('old-abi',{0:0x50455670})]
 changes += [('packet-'+str(i),{L['DAMAGE_DEFINITION_BASE']+i:1}) for i in range(8)]
 for name,bits in [('nan',[0,0x7ff80000]),('inf',[0,0x7ff00000]),('negative-inf',[0,0xfff00000])]:changes.append((name,{d+F['VALUE']:bits[0],d+F['VALUE']+1:bits[1]}))
 programs=[];rows=[]
 for name,updates in changes:
  words=source.copy()
  for p,v in updates.items():words[p]=v
  programs.append((words,copy.deepcopy(metadata)));rows.append(dict(name='hp-attack-invalid-'+name,status=64))
 for value in (1e308,-1e308):
  words=source.copy();words[d+F['VALUE']:d+F['VALUE']+2]=double_words(value)
  programs.append((words,copy.deepcopy(metadata)));rows.append(dict(name='hp-attack-arithmetic-overflow-'+str(value),status=16))
 return programs,rows
