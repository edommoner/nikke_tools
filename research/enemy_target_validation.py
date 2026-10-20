"""Raw GPU admission boundaries for victim rules;shared across CUDA/Metal."""
import copy
from portable_specs import LIMITS as L,FIELDS as F
from portable_enemy_target_specs import META_BASE as M,COMMAND_BASE as B
from portable_runtime import double_words

def programs(cases,compile_case):
 words,meta=compile_case(cases[0]);step=next(i for i,c in enumerate(cases[0]['script']) if c[1]==32);d=B+step*4;cmd=L['COMMAND_BASE']+step*8;incoming=L['INCOMING_BASE']+step*4;definition=L['DEFINITION_BASE']
 changes=[('enable-flag',{M:2}),('missing-policy',{M:0}),('missing-policy-with-seed',{M:0,M+1:1}),('noncombat',{3:0}),('unused-descriptor',{B:1}),('rule',{d:4}),('random-zero-count',{d:2,d+1:0}),('random-large-count',{d:2,d+1:6}),('random-slots',{d:2,d+1:1,d+2:1}),('all-count',{d+1:1}),('all-slots',{d+2:1}),('all-ignore-taunt',{d+3:1}),('flags',{d+3:2}),('marker-kind',{definition+F['KIND']:4}),('marker-damage-flags',{definition+F['DAMAGE_FLAGS']:1}),('marker-extra-packet',{L['DAMAGE_DEFINITION_BASE']:1}),('pierce-flag',{cmd+3:2}),('cpu-cover-mask',{cmd+4:1}),('cpu-selected-mask',{cmd+5:1}),('command-reserved6',{cmd+6:1}),('command-reserved7',{cmd+7:1}),('old-abi',{0:0x50455672})]
 for i in range(3,8):changes.append(('meta-reserved-'+str(i),{M+i:1}))
 for name,count,slots in [('empty',0,0),('missing',2,1),('duplicate',2,1|(1<<3)),('unsorted',2,3|(1<<3)),('outside',1,6),('trailing',1,1|(2<<3)),('high-bit',1,1|(1<<15))]:changes.append(('slot-'+name,{d:1,d+1:count,d+2:slots}))
 for name,value,offset in [('negative-attack',-1,0),('large-attack',1e31,0),('negative-coefficient',-1,2),('large-coefficient',1000001,2)]:
  lo,hi=double_words(value);changes.append((name,{incoming+offset:lo,incoming+offset+1:hi}))
 for name,hi in [('nan',0x7ff80000),('infinity',0x7ff00000)]:changes.append(('attack-'+name,{incoming:0,incoming+1:hi}))
 out=[];rows=[]
 for name,updates in changes:
  w=words.copy()
  for position,value in updates.items():w[position]=value
  out.append((w,copy.deepcopy(meta)));rows.append(dict(name='enemy-target-invalid-'+name,status=64))
 return out,rows
