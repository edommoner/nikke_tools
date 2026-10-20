"""Typed128 stack controls use the existing numeric and deferred notice loop."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_specs import LIMITS as L
from portable_backend import execute,source_hashes
from portable_stack_specs import plan
import world_actor_stack_cases as cases
s=importlib.util.spec_from_file_location('typed_stack_status',ROOT/'research/verify-world-actor-status.py');status=importlib.util.module_from_spec(s);s.loader.exec_module(status)
SOURCE='gpu/world_actor_stack_entry.slang';MAGIC=0x57543031

def fixtures():return cases.fixtures(status)
def compile_case(c):
 w,m,b=status.compile_case(c);w[0]=L['WORLD_ACTOR_STACK_ABI'];w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4]=MAGIC
 for i,e in enumerate(c['effects']):
  p=plan(e,combat=c['combat'])
  if p is not None and p[1]==2 and p[2][0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 return w,m,b

decoded=status.decoded

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0]
 for name,at,value in [('unknown-stack-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57543032),('stack-control-disabled-in-status-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57493031),('stack-nonfinite-delta',L['DEFINITION_BASE']+32+7,0x7ff00000),('stack-route-overflow',L['DAMAGE_DEFINITION_BASE']+8,10),('stack-scope-count-zero',L['DAMAGE_DEFINITION_BASE']+9,0),('stack-scope-count-overflow',L['DAMAGE_DEFINITION_BASE']+9,257),('stack-packet-reserved',L['DAMAGE_DEFINITION_BASE']+10,1)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 import copy
 edge=copy.deepcopy(next(c for c in rows if c['name']=='unlimited-last-exact31bit-stack'));edge['effects'][1]['fixed_value']=2147483647;ew,_,_=compile_case(edge);bad.append(('unlimited-stack-exceeds31bit-storage',ew))
 return rows,programs,bad

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows,programs,bad=prepare();native=[status.recipient.state.fields.pool.observe(c) for c in rows]
 if a.cpu_only:
  (ROOT/'research/portable-build/world-actor-stack-native.json').write_text(json.dumps(dict(names=[c['name'] for c in rows],cases=native),ensure_ascii=False,indent=2)+'\n');print('CPU typed stack native',len(rows),'raw',len(bad),'GPU0');return
 old=json.loads((ROOT/'research/portable-world-actor-status-metal.json').read_text());op=Path(old['captured']);before=(op/'input.bin').read_bytes();beforeout=(op/'readback.bin').read_bytes();n=int.from_bytes(before[:4],'little');assert n==529;iw=92336*4;ow=524288*4
 packed=array.array('I',[len(rows)+len(bad)+n])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 for i in range(n):
  w=list(struct.unpack_from('<'+'I'*92336,before,4+i*iw));w[0]=L['WORLD_ACTOR_STACK_ABI'];packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.replay:
  folder=a.replay;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert (folder/'input.bin').read_bytes()==data and evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-actor-stack-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,92336,524288,a.backend)
  except Exception as err:(folder/'failure.json').write_text(json.dumps(dict(error=repr(err),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,(c,(_,m,b),expected) in enumerate(zip(rows,programs,native)):
  block=values[i*524288:(i+1)*524288]
  try:actual=decoded(block,m,c,b);changed=[k for k in expected if k!='scope' and actual[k]!=expected[k]]
  except Exception as err:actual=dict(status=block[0],decode_error=repr(err));changed=['decode']
  results.append(dict(name=c['name'],passed=block[0]==0 and not changed,changed=changed,actual=actual,native=expected))
 rejected=[dict(name=name,status=values[(len(rows)+j)*524288],passed=values[(len(rows)+j)*524288]==(2 if name=='unlimited-stack-exceeds31bit-storage' else 64)) for j,(name,_) in enumerate(bad)]
 prior=[dict(index=j,passed=raw[(len(rows)+len(bad)+j)*ow:(len(rows)+len(bad)+j+1)*ow]==beforeout[j*ow:(j+1)*ow]) for j in range(n)]
 report=dict(passed=all(x['passed'] for x in results+rejected+prior),cases=results,rejected_cases=rejected,preserved529=prior,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),cpu_state_used_as_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-actor-stack-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[x.get('name',x.get('index')) for x in results+rejected+prior if not x['passed']];print('Typed stack native',len(rows),'raw',len(bad),'old529 exact',a.backend)
if __name__=='__main__':main()
