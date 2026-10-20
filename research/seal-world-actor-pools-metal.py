"""Audit frozen full128 HP raw/provenance and actual native oracle without GPU."""
import array,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
SOURCE='822c559508f660c33376385094a97645f509e3bd'
def sha(x):return hashlib.sha256(x).hexdigest()
def load(n):return json.loads((ROOT/'research'/n).read_text())
def module(n,p):
 s=importlib.util.spec_from_file_location(n,ROOT/p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def main():
 d=module('pool_proof_driver','research/verify-world-actor-pools.py');L=d.L;r=load('portable-world-actor-pools-metal.json');p=Path(r['captured']);data=(p/'input.bin').read_bytes();raw=(p/'readback.bin').read_bytes();e=r['evidence'];iw=L['WORLD_ACTOR_POOL_INPUT_WORDS']*4;ow=L['WORLD_ACTOR_POOL_OUTPUT_WORDS']*4
 assert r['source_commit']==SOURCE and r['passed'] and e['gpu_execution_verified'] and e['backend']=='metal';assert struct.unpack_from('<I',data)[0]==285 and len(data)==4+285*iw and len(raw)==285*ow
 assert sha(data)==e['input_sha256'] and sha(raw)==e['output_sha256'];assert e==json.loads((p/'evidence.json').read_text())
 for name,h in e['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+name],cwd=ROOT))==h
 rows,programs,bad=d.prepare();assert (len(rows),len(bad),len(r['preserved242']))==(24,19,242)
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 fingerprints=[]
 for i,(case,(words,meta,bindings),stored) in enumerate(zip(rows,programs,r['cases'])):
  assert data[4+i*iw:4+(i+1)*iw]==struct.pack('<'+'I'*len(words),*words)
  block=values[i*ow//4:(i+1)*ow//4];actual=d.manual.decoded(block,case,L,bindings) if 'actions' in case else d.decoded(block,meta,case,bindings);native=d.manual.native(case,L) if 'actions' in case else d.observe(case)
  assert stored['passed'] and stored['actual']==json.loads(json.dumps(actual)) and stored['native']==json.loads(json.dumps(native)) and all(actual[k]==native[k] for k in native if k!='scope') and block[0]==0,case['name']
 for j,((name,words),stored) in enumerate(zip(bad,r['rejected_cases'])):
  i=24+j;assert data[4+i*iw:4+(i+1)*iw]==struct.pack('<'+'I'*len(words),*words) and values[i*ow//4]==64 and stored['name']==name and stored['passed']
 old=load('portable-world-actors-metal.json');oldp=Path(old['captured']);before=(oldp/'readback.bin').read_bytes();oldinput=(oldp/'input.bin').read_bytes();assert sha(before)==old['evidence']['output_sha256'] and sha(oldinput)==old['evidence']['input_sha256'];oldiw=90536*4;oldow=225280*4
 for j,stored in enumerate(r['preserved242']):
  i=43+j;newblock=raw[i*ow:(i+1)*ow];assert newblock[:oldow]==before[j*oldow:(j+1)*oldow] and not any(newblock[oldow:]) and stored['passed'];assert sha(newblock)==stored['output_sha256']
  incoming=bytearray(data[4+i*iw:4+(i+1)*iw]);incoming[:4]=(0x50455676).to_bytes(4,'little');assert incoming[:oldiw]==oldinput[4+j*oldiw:4+(j+1)*oldiw] and not any(incoming[oldiw:])
 normal=json.loads((ROOT/'research/portable-build/world-actor-pools-default-parity.json').read_text());assert normal['passed'] and normal['actual']==normal['expected'];assert normal['source_sha256']=={k:v for k,v in e['source_sha256'].items() if k!='gpu/world_actor_pool_entry.slang'}
 log=(ROOT/'research/portable-build/world-actor-pools-unit.log').read_bytes();assert b'Ran 309 tests' in log and log.rstrip().endswith(b'OK')
 for i in range(285):fingerprints.append(dict(index=i,input_sha256=sha(data[4+i*iw:4+(i+1)*iw]),output_sha256=sha(raw[i*ow:(i+1)*ow])))
 result=dict(passed=True,source_commit=SOURCE,metal_device=e['transport']['device'],metal_inputs=285,complete_native_battles=14,typed_native_pool_set_cases=10,raw_rejections=19,previous242_entire_outputs_preserved=True,source_blob_verified=True,normal_generated_cuda_msl_exact=True,cpu_tests=309,cpu_log_sha256=sha(log),input_sha256=sha(data),output_sha256=sha(raw),actor_slots=128,owned_target_sets=32,physical_actor_landing_connected=True,windows_actor_verified=False,wide_enemy_effects_connected=False,canonical_world_admission=False,normal_ui='CPU',full_character_verified=0,full_goal_complete=False,audit_gpu_calls=0)
 (ROOT/'research/portable-world-actor-pools-validation.json').write_text(json.dumps(result,indent=2)+'\n');(ROOT/'research/portable-world-actor-pools-fingerprints.json').write_text(json.dumps(dict(source_sha256=e['source_sha256'],cases=fingerprints),indent=2)+'\n');print('Actor pools Metal285 audited: native14+typed10+raw19+old242,CPU309;GPU calls0')
if __name__=='__main__':main()
