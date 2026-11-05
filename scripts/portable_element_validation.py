"""Malformed element-override wire inputs, shared by CUDA and Metal."""
def rejection_programs(cases,compile_case):
 from portable_specs import LIMITS as L,FIELDS as F
 c=next(c for c in cases if c['name']=='element-matrix-2-2-False');base=L['DEFINITION_BASE']+L['DEFINITION_WORDS'];packet=L['DAMAGE_DEFINITION_BASE']+L['DAMAGE_DEFINITION_WORDS'];world=L['WORLD_META_BASE']
 inputs=[];rows=[]
 def add(name,changes):
  p,m=compile_case(c)
  for at,value in changes:p[at]=value
  inputs.append((p,m));rows.append(dict(name='wire-element-'+name,status=64))
 p,_=compile_case(c);names=p[world+1]
 for name,changes in [
  ('missing-count',[(world+2,0)]),('wrong-count',[(world+2,2)]),('count-overflow',[(world+2,257)]),('reserved-world',[(world+3,1)]),
  ('unknown-code',[(packet,names+1)]),('code-overflow',[(packet,257)]),('empty-name-pool',[(world,0),(world+1,0)]),
  ('wrong-kind',[(base+F['KIND'],4)]),('damage-kind',[(base+F['KIND'],3)]),('wrong-stat',[(base+F['STAT'],0)]),
  ('numeric-payload',[(base+F['VALUE'],1)]),('damage-flags',[(base+F['DAMAGE_FLAGS'],1)]),
  ('enemy-policy',[(L['HEALTH_DEFINITION_BASE']+L['HEALTH_DEFINITION_WORDS']+3,1)])]:add(name,changes)
 for field in range(1,8):add('packet-reserved-'+str(field),[(packet+field,1)])
 return inputs,rows
