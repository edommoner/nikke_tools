"""Boss victim rules and seed input; no CPU-resolved targets or RNG state."""
import re
from portable_specs import LIMITS as L
ABI=0x50455673
META_BASE=L['BURST_REFERENCE_BASE']+L['BURST_REFERENCE_WORDS']
COMMAND_BASE=META_BASE+8
RNG_BASE=(L['PROTECTION_BUILD_BASE']+10+7)//8*8
RNG_WORDS=632
QUERY_BASE=RNG_BASE+RNG_WORDS
assert COMMAND_BASE+L['COMMANDS']*4<=L['INPUT_WORDS']
assert QUERY_BASE+L['COMMANDS']*8<=L['SPLIT_HIT_BASE']
STATS={'stealth':65,'taunt':66}

def target_rule(spec):
 if not isinstance(spec,dict) or set(spec)-{'target','ignore_taunt'}:raise ValueError('Invalid enemy victim rule')
 target=spec.get('target');ignore=spec.get('ignore_taunt',False)
 if not isinstance(target,str) or type(ignore) is not bool:raise ValueError('Invalid enemy target/taunt policy')
 if target=='all':
  if ignore:raise ValueError('All-target rule already ignores taunt')
  return [0,0,0,0]
 match=re.fullmatch(r'(random|top_atk):([0-9]+)',target)
 if match:
  n=int(match[2])
  if n<1:raise ValueError('Enemy victim count must be positive')
  return [2 if match[1]=='random' else 3,min(n,5),0,int(ignore)]
 if target.startswith('slot:'):
  raw=target[5:].split(',')
  if not all(re.fullmatch(r'\s*[0-9]+\s*',v) for v in raw):raise ValueError('Invalid fixed enemy slots')
  slots=sorted(set(int(v)-1 for v in raw))
  if not slots or min(slots)<0 or max(slots)>4:raise ValueError('Enemy slot outside five-member squad')
  return [1,len(slots),sum((who+1)<<(3*i) for i,who in enumerate(slots)),int(ignore)]
 raise ValueError('Unported enemy victim rule')

def pack(words,config,script,effects):
 steps=[i for i,c in enumerate(script) if c[1]==32]
 markers=any(e.get('type')=='buff' and e.get('stat') in STATS for e,_ in effects)
 enabled=bool(steps or markers)
 if not enabled:
  if config is not None:raise ValueError('Enemy targeting policy has no consuming feature')
  return dict(enabled=False,steps=[])
 if config is None:config={}
 if not isinstance(config,dict) or set(config)-{'seed','attacks'}:raise ValueError('Invalid GPU enemy targeting configuration')
 seed=config.get('seed',0)
 if type(seed) is not int or not 0<=seed<2**64:raise ValueError('Enemy RNG seed must be an unsigned64 integer')
 authored=config.get('attacks',{})
 if not isinstance(authored,dict):raise ValueError('Enemy attack rules must be indexed by command')
 rules={}
 for key,value in authored.items():
  if type(key) is int:index=key
  elif isinstance(key,str) and key.isascii() and key.isdigit() and str(int(key))==key:index=int(key)
  else:raise ValueError('Invalid enemy attack command index')
  if index in rules:raise ValueError('Duplicate enemy attack command index')
  rules[index]=target_rule(value)
 if set(rules)!=set(steps):raise ValueError('Every enemy attack needs exactly one authored victim rule')
 words[META_BASE:META_BASE+8]=[1,seed&0xffffffff,seed>>32,0,0,0,0,0]
 for step,descriptor in rules.items():words[COMMAND_BASE+step*4:COMMAND_BASE+step*4+4]=descriptor
 return dict(enabled=True,steps=steps,seed=seed,rules=rules)
