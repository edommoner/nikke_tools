"""Shared GPU uint RNG probe versus original CPython Random; authored seeds/operations only."""
import argparse,array,datetime,hashlib,json,random,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'app'))
from portable_backend import execute
class Observer(random.Random):
 def __init__(self,seed):self.draws=0;self.rejects=0;self.samples=0;super().__init__(seed)
 def getrandbits(self,k):
  self.draws+=int(k!=0);return super().getrandbits(k)
 def _randbelow(self,n):
  start=self.draws;value=random.Random._randbelow_with_getrandbits(self,n);self.rejects+=self.draws-start-1;return value

def fixtures():
 seeds=[0,1,19,2**31-1,2**31,2**32-1,2**32,2**32+1,2**63,2**64-1,0x0123456789abcdef,0xfedcba9876543210]
 pattern=[32,1<<24|5,2<<24|5<<8|5,1,1<<24|1,2<<24|5<<8|3,0,2<<24]
 rows=[dict(name=f'mt-mixed-{seed}',seed=seed,ops=pattern*128) for seed in seeds]
 for seed in (0,19,2**64-1):
  for count in (0,1,623,624,625,1024):rows.append(dict(name=f'mt-raw-{seed}-{count}',seed=seed,ops=[32]*count))
 # Every small population/request count,including deterministic singleton and empty samples.
 samples=[2<<24|n<<8|k for n in range(6) for k in range(n+1)]
 rows.append(dict(name='mt-small-pools',seed=0,ops=(samples*48)[:1024]))
 return rows

def native(case):
 rng=Observer(case['seed']);values=[]
 for op in case['ops']:
  kind=op>>24;arg=op&0xffffff;mask=0
  if kind==0:value=rng.getrandbits(arg)
  elif kind==1:value=rng._randbelow(arg)
  else:
   rng.samples+=1;selected=rng.sample(list(range(arg>>8)),arg&255);value=sum((who+1)<<(3*i) for i,who in enumerate(selected));mask=sum(1<<who for who in selected)
  values.append([value,mask])
 state=rng.getstate()[1]
 return dict(values=values,index=state[-1],state=list(state[:-1]),draws=rng.draws,rejects=rng.rejects,samples=rng.samples)
