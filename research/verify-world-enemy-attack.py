"""One native oracle and literal input suite for CUDA/Metal enemy attack fields."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
from world_frame_native import observe
import world_enemy_attack_cases as cases
s=importlib.util.spec_from_file_location('enemy_attack_physical','research/verify-world-counter-landings.py');physical=importlib.util.module_from_spec(s);s.loader.exec_module(physical)
SOURCE='gpu/world_enemy_attack_entry.slang';OUTPUT=L['WORLD_PERIODIC_OUTPUT_WORDS']
def fixtures():return cases.fixtures()
def compile_case(case):
 w,m,b=physical.pack.compile_case(case,allow_no_counter=True);w[0]=L['WORLD_ENEMY_ATTACK_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=13;return w,m,b
def decoded(block,meta,case,bindings):
 r=physical.decoded(block,meta,case,bindings);r['enemy_attack_fields']=[dict(kind=int(b.kind),identity=b.identity,flat=struct.unpack('<d',struct.pack('<II',*block[L['WORLD_ENEMY_ATTACK_BASE']+i*2:L['WORLD_ENEMY_ATTACK_BASE']+(i+1)*2]))[0]) for i,b in enumerate(bindings)];return r
def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];seed=programs[1][0];bad=[];d=L['DEFINITION_BASE']
 for name,at,value in [('enemy-attack-old-mode11',L['TARGET_COUNTER_INPUT_BASE']+6,11),('enemy-attack-unknown-mode14',L['TARGET_COUNTER_INPUT_BASE']+6,14),('enemy-attack-stat-overflow',d+F['STAT'],100),('enemy-attack-recipient-overflow',L['DAMAGE_DEFINITION_BASE']+1,257),('enemy-attack-route-overflow',L['DAMAGE_DEFINITION_BASE'],10),('enemy-attack-without-landings',L['LANDING_META_BASE'],0),('enemy-attack-with-bullet-duration',L['BULLET_DEFINITION_BASE'],1)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args()
 rows,programs,bad=prepare();native=[observe(c) for c in rows]
 if a.cpu_only:print('Enemy attack native',len(rows),'raw',len(bad),'GPU0');return
 packed=array.array('I',[len(rows)+len(bad)])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes();ow=OUTPUT*4
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();e=json.loads((folder/'evidence.json').read_text());assert e['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-enemy-attack-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,e=execute(SOURCE,'portableEvents',data,97464,OUTPUT,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
 checked=[]
 for i,(c,(_,m,b),n) in enumerate(zip(rows,programs,native)):
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  try:r=decoded(block,m,c,b);changed=[k for k in n if k!='scope' and r[k]!=n[k]]
  except Exception as error:r=dict(error=repr(error));changed=['decode']
  checked.append(dict(name=c['name'],passed=block[0]==0 and not changed,status=block[0],changed=changed,actual=r,native=n))
 rejected=[dict(name=name,status=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little'),passed=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little')==64) for i,(name,_) in enumerate(bad)]
 report=dict(passed=all(c['passed'] for c in checked+rejected),cases=checked,rejected_cases=rejected,captured=str(folder),evidence=e,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),unchanged_gpu_retries=0,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-enemy-attack-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[(c['name'],c.get('changed'),c['status']) for c in checked+rejected if not c['passed']];print('Enemy attack',len(rows),'native',len(bad),'raw',a.backend)
if __name__=='__main__':main()
