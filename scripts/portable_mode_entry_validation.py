"""Shared raw admission checks for measured mode-entry delay fields."""
import copy
from portable_specs import LIMITS as L,FIELDS as F
from portable_runtime import double_words

def rejection_programs(cases,compile_case):
 c=next(c for c in cases if c.get('mode_entry_reference'));w,m=compile_case(c);pos=L['MODE_BASE']+2*L['MODE_WORDS']+28;d=L['DEFINITION_BASE']+2*L['DEFINITION_WORDS']
 variants=[('flag',{pos+2:2}),('reserved',{pos+3:1}),('missing-flag',{pos:double_words(.39)[0],pos+1:double_words(.39)[1],pos+2:0}),('kind',{d+F['KIND']:0}),('noncombat',{3:0}),('nonmode-payload',{L['MODE_BASE']+30:1}),('old-abi',{0:0x50455671})]
 for label,value in [('negative',-1),('nan',None),('inf',None),('large',181)]:
  bits=[0,0x7ff80000] if label=='nan' else [0,0x7ff00000] if label=='inf' else double_words(value);variants.append((label,{pos:bits[0],pos+1:bits[1]}))
 programs=[];rows=[]
 for label,updates in variants:
  words=w.copy()
  for p,v in updates.items():words[p]=v
  programs.append((words,copy.deepcopy(m)));rows.append(dict(name='mode-entry-invalid-'+label,status=64))
 return programs,rows
