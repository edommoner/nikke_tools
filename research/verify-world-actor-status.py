"""Typed128 immunity and cleanse use the existing common status loop."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_specs import LIMITS as L
from portable_backend import execute,source_hashes
from portable_status_specs import cleanse_plan
import world_actor_status_cases as cases
s=importlib.util.spec_from_file_location('wide_status_recipients',ROOT/'research/verify-world-actor-recipients.py');recipient=importlib.util.module_from_spec(s);s.loader.exec_module(recipient)
SOURCE='gpu/world_actor_status_entry.slang';MAGIC=0x57493031

def fixtures():return cases.fixtures(recipient)
def compile_case(c):
 w,m,b=recipient.compile_case(c);w[0]=L['WORLD_ACTOR_STATUS_ABI'];w[L['WORLD_ACTOR_POOL_INPUT_BASE']+4]=MAGIC
 for i,e in enumerate(c['effects']):
  p=cleanse_plan(e,combat=c['combat'])
  if p is not None and p[0]==2 and p[1][0]==2:w[L['DAMAGE_DEFINITION_BASE']+i*8+1]=128
 return w,m,b

def decoded(block,meta,c,bindings):
 actual=recipient.decoded(block,meta,c,bindings);used=[]
 for name,index in meta['states'].items():
  for who in range(5+len(bindings)):
   at=(L['IMMUNITY_USED_BASE']+(who*256+index)*2) if who<5 else (L['WORLD_ACTOR_WIDE_IMMUNITY_BASE']+((who-5)*256+index)*2)
   value=struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
   if value:
    actor=[-1,who] if who<5 else [int(bindings[who-5].kind),bindings[who-5].identity];used.append(dict(actor=actor,name=name,used=value))
 actual['enemy_fields']['nonzero_immunity_used']=sorted(used,key=lambda x:(x['actor'],x['name']));return actual

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];seed=programs[0][0]
 for name,at,value in [('unknown-status-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57493032),('enemy-immunity-disabled-in-recipient-policy',L['WORLD_ACTOR_POOL_INPUT_BASE']+4,0x57523031),('count-nonfinite-capacity',L['DEFINITION_BASE']+7,0x7ff00000)]:
  w=list(compile_case(next(c for c in rows if c['name']=='128-count-immunity-2'))[0] if name=='count-nonfinite-capacity' else seed);w[at]=value;bad.append((name,w))
 c=next(c for c in rows if c['name']=='typed-cleanse-scope-enemies_top_hp:2');cw,_,_=compile_case(c)
 for name,at,value in [('cleanse-route-overflow',L['DAMAGE_DEFINITION_BASE']+8,10),('cleanse-count-zero',L['DAMAGE_DEFINITION_BASE']+9,0),('cleanse-count-overflow',L['DAMAGE_DEFINITION_BASE']+9,257),('cleanse-packet-reserved',L['DAMAGE_DEFINITION_BASE']+10,1)]:
  w=list(cw);w[at]=value;bad.append((name,w))
 import copy
 hit=copy.deepcopy(c);hit['patterns'][0]['spec'].pop('hp',None);hit['patterns'][0]['spec']['hit_hp']=2;hw,_,_=compile_case(hit);bad.append(('pure-hit-hp-max-rank-unresolved-native-contract',hw))
 return rows,programs,bad

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows,programs,bad=prepare();native=[recipient.state.fields.pool.observe(c) for c in rows]
 if a.cpu_only:
  (ROOT/'research/portable-build/world-actor-status-native.json').write_text(json.dumps(dict(names=[c['name'] for c in rows],cases=native),ensure_ascii=False,indent=2)+'\n');print('CPU typed status native',len(rows),'raw',len(bad),'GPU0');return
 old=json.loads((ROOT/'research/portable-world-actor-recipient-metal.json').read_text());op=Path(old['captured']);before=(op/'input.bin').read_bytes();beforeout=(op/'readback.bin').read_bytes();n=int.from_bytes(before[:4],'little');assert n==484;iw=92336*4;ow=524288*4
 packed=array.array('I',[len(rows)+len(bad)+n])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 for i in range(n):
  w=list(struct.unpack_from('<'+'I'*92336,before,4+i*iw));w[0]=L['WORLD_ACTOR_STATUS_ABI'];packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.replay:
  folder=a.replay;raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert (folder/'input.bin').read_bytes()==data and evidence['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-actor-status-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data)
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
 rejected=[dict(name=name,status=values[(len(rows)+j)*524288],passed=values[(len(rows)+j)*524288]==64) for j,(name,_) in enumerate(bad)]
 prior=[dict(index=j,passed=raw[(len(rows)+len(bad)+j)*ow:(len(rows)+len(bad)+j+1)*ow]==beforeout[j*ow:(j+1)*ow]) for j in range(n)]
 report=dict(passed=all(x['passed'] for x in results+rejected+prior),cases=results,rejected_cases=rejected,preserved484=prior,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),cpu_state_used_as_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-actor-status-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[x.get('name',x.get('index')) for x in results+rejected+prior if not x['passed']];print('Typed status native',len(rows),'raw',len(bad),'old484 exact',a.backend)
if __name__=='__main__':main()
