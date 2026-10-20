"""Typed named removal from the canonical resident executor versus native."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_specs import LIMITS as L
from portable_backend import execute,source_hashes
from portable_removal_specs import plan
import world_actor_mutation_cases as cases
s=importlib.util.spec_from_file_location('mutation_state',ROOT/'research/verify-world-actor-state.py');state=importlib.util.module_from_spec(s);s.loader.exec_module(state)
SOURCE='gpu/world_actor_mutation_entry.slang';MAGIC=0x574D3031

def fixtures():return cases.fixtures(state)
def compile_case(c):
 w,m,b=state.compile_case(c);w[0]=L['WORLD_ACTOR_MUTATION_ABI'];w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4]=MAGIC
 for i,e in enumerate(c['effects']):
  p=plan(e,combat=c['combat'])
  if p is not None and p[0]==2 and p[1][0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 return w,m,b

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0];row=1;d=L['DEFINITION_BASE']+row*32;packet=L['DAMAGE_DEFINITION_BASE']+row*8
 for name,at,value in [('unknown-mutation-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x574D3032),('removal-disabled-in-state-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57533031),('removal-scope-overflow',d+21,3),('enemy-route-overflow',packet,10),('enemy-count-zero',packet+1,0),('enemy-count-overflow',packet+1,257),('enemy-packet-reserved',packet+2,1)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows,programs,bad=prepare();native=[state.fields.pool.observe(c) for c in rows]
 if a.cpu_only:
  (ROOT/'research/portable-build/world-actor-mutation-native.json').write_text(json.dumps(dict(names=[c['name'] for c in rows],cases=native),ensure_ascii=False,indent=2)+'\n');print('CPU native',len(rows),'raw',len(bad),'GPU calls0');return
 old=json.loads((ROOT/'research/portable-world-actor-state-metal.json').read_text());op=Path(old['captured']);before=(op/'input.bin').read_bytes();beforeout=(op/'readback.bin').read_bytes();n=int.from_bytes(before[:4],'little');assert n==424;iw=92336*4;ow=262144*4
 packed=array.array('I',[len(rows)+len(bad)+n])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 for i in range(n):
  w=list(struct.unpack_from('<'+'I'*92336,before,4+i*iw));w[0]=L['WORLD_ACTOR_MUTATION_ABI'];packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.replay:
  folder=a.replay;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert (folder/'input.bin').read_bytes()==data and evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-actor-mutation-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,92336,262144,a.backend)
  except Exception as err:(folder/'failure.json').write_text(json.dumps(dict(error=repr(err),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,(c,(_,m,b),expected) in enumerate(zip(rows,programs,native)):
  block=values[i*262144:(i+1)*262144]
  try:actual=state.decoded(block,m,c,b);changed=[k for k in expected if k!='scope' and actual[k]!=expected[k]]
  except Exception as err:actual=dict(status=block[0],decode_error=repr(err));changed=['decode']
  results.append(dict(name=c['name'],passed=block[0]==0 and not changed,changed=changed,actual=actual,native=expected))
 rejected=[dict(name=name,status=values[(len(rows)+j)*262144],passed=values[(len(rows)+j)*262144]==64) for j,(name,_) in enumerate(bad)]
 prior=[dict(index=j,passed=raw[(len(rows)+len(bad)+j)*ow:(len(rows)+len(bad)+j+1)*ow]==beforeout[j*ow:(j+1)*ow]) for j in range(n)]
 report=dict(passed=all(x['passed'] for x in results+rejected+prior),cases=results,rejected_cases=rejected,preserved424=prior,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),cpu_state_used_as_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-actor-mutation-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[x.get('name',x.get('index')) for x in results+rejected+prior if not x['passed']];print('Mutation native',len(rows),'raw',len(bad),'old424 exact',a.backend)
if __name__=='__main__':main()
