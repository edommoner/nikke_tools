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

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['metal','cuda'],default='metal');p.add_argument('--native-only',action='store_true');a=p.parse_args();cases=fixtures();words=array.array('I',[len(cases)])
 for c in cases:
  packed=[0x4d543031,c['seed']&0xffffffff,c['seed']>>32,len(c['ops']),0,0,0,0,*c['ops']];packed.extend([0]*(1032-len(packed)));assert len(packed)==1032;words.extend(packed)
 if sys.byteorder!='little':words.byteswap()
 raw=None;evidence={};folder=None
 if not a.native_only:
  folder=ROOT/'research/portable-build'/('target-rng-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
  data=words.tobytes();(folder/'input.bin').write_bytes(data)
  raw,evidence=execute('gpu/mt19937_probe.slang','mtProbe',data,1032,4096,a.backend)
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
  gpu=array.array('I');gpu.frombytes(raw)
  if sys.byteorder!='little':gpu.byteswap()
 rows=[]
 for i,c in enumerate(cases):
  expected=native(c);actual=None
  try:
   assert expected['draws']>=len([op for op in c['ops'] if op>>24==0 and op!=0])
   if raw is not None:
    block=gpu[i*4096:(i+1)*4096];assert block[0]==0 and block[1]==len(c['ops'])
    base=3072;actual=dict(values=[list(block[4+j*2:6+j*2]) for j in range(len(c['ops']))],index=block[base],draws=block[base+1],samples=block[base+2],rejects=block[base+3],state=list(block[base+8:base+632]))
    assert actual==expected,'Full RNG values,state,index or consumption differs'
  except Exception as error:rows.append(dict(name=c['name'],passed=False,error=repr(error),native=expected,actual=actual))
  else:rows.append(dict(name=c['name'],passed=True,native=expected,actual=actual))
 report=dict(passed=all(r['passed'] for r in rows),cases=rows,captured=str(folder) if folder else None,source_sha256_local={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('gpu/portable_mt19937.slang','gpu/mt19937_probe.slang','research/verify-target-rng.py')},python_version=sys.version,cpu_selected_targets_used_as_gpu_input=False,cpu_rng_state_used_as_gpu_input=False,scope='31 uint64-seed/sequence RNG cases,all draw results and624-word final MT state,index,draw/rejection/sample counts; no production combat/taunt admission yet',**evidence)
 suffix='native' if a.native_only else a.backend
 (ROOT/f'research/portable-target-rng-{suffix}.json').write_text(json.dumps(report,indent=2)+'\n')
 assert report['passed'],[(r['name'],r.get('error')) for r in rows if not r['passed']]
 print(len(rows),'original CPython RNG sequences match',suffix)
if __name__=='__main__':main()
