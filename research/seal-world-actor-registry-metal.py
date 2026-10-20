"""Frozen Actor ABI76 lifecycle proof;no additional GPU execution."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];SOURCE='14fab0863a3fced96737635f50126a8d9139cdef'
def load(name):return json.loads((ROOT/'research'/name).read_text())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def groups(r):return [r['cases'],r['rejected_cases'],r['preserved208']]
def captured(r):
 p=Path(r['captured']);i=(p/'input.bin').read_bytes();o=(p/'readback.bin').read_bytes();n=sum(len(x) for x in groups(r));assert int.from_bytes(i[:4],'little')==n and len(i)==4+n*90536*4 and len(o)==n*225280*4;assert sha(i)==r['evidence']['input_sha256'] and sha(o)==r['evidence']['output_sha256'];return i,o
def main():
 r=load('portable-world-actors-metal.json');old=load('portable-world-actors-initial-metal.json');golden=load('portable-world-charge-hold-expected.json');normal=load('portable-world-actor-default-generated-parity.json');data,raw=captured(r);oi,oo=captured(old);iw=90536*4;ow=225280*4
 assert r['passed'] and len(r['cases'])==12 and len(r['rejected_cases'])==22 and len(r['preserved208'])==208 and all(x['passed'] for g in groups(r) for x in g)
 assert normal['source_sha256']=={k:v for k,v in r['evidence']['source_sha256'].items() if k!='gpu/world_actor_entry.slang'}
 assert normal['passed'] and normal['actual']==normal['expected'] and not r['actor_hp_landing_connected'] and not r['actor_enemy_count_policy_connected']
 for path,h in r['evidence']['source_sha256'].items():assert sha(subprocess.check_output(['git','show',SOURCE+':'+path],cwd=ROOT))==h
 mapping={};offset=0;fingerprints=[]
 for domain,g in enumerate(groups(r)):
  for row in g:
   mapping[domain,row['name']]=(offset,row);fingerprints.append(dict(domain=domain,name=row['name'],input_sha256=sha(data[4+offset*iw:4+(offset+1)*iw]),output_sha256=sha(raw[offset*ow:(offset+1)*ow]),semantic_sha256=sha(json.dumps(row,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode())));offset+=1
 offset=0
 for domain,g in enumerate(groups(old)):
  for row in g:
   j,new=mapping[domain,row['name']];assert data[4+j*iw:4+(j+1)*iw]==oi[4+offset*iw:4+(offset+1)*iw] and raw[j*ow:(j+1)*ow]==oo[offset*ow:(offset+1)*ow]
   if domain==0:assert new['native']==row['native'] and new['actual']==row['actual']
   offset+=1
 for i,(actual,expected) in enumerate(zip(r['preserved208'],golden['comparison']['cases'])):
  assert actual['name']==expected['name'] and actual['output_sha256']==expected['output_sha256']
  # Only ABI word and an all-zero actor extension differ from the old input.
  j,_=mapping[2,actual['name']];block=data[4+j*iw:4+(j+1)*iw];prefix=bytearray(block[:89376*4]);prefix[:4]=(0x50455675).to_bytes(4,'little');assert sha(prefix)==expected['input_sha256'] and not any(block[89376*4:])
 log=ROOT/'research/portable-build/world-actor-unit-final.log';assert 'Ran 303 tests' in log.read_text() and log.read_text().rstrip().endswith('OK')
 result=dict(cpu_log_sha256=sha(log.read_bytes()),passed=True,source_commit=SOURCE,metal_inputs=242,native_registry_cases=12,raw_rejections=22,old208_full_outputs_preserved=True,initial237_full_input_output_blocks_preserved=True,normal_cuda_msl_generated_exact=True,input_sha256=sha(data),output_sha256=sha(raw),max_registry_slots=128,actual_boss_and_registry_oracle=True,cpu_tests=303,actor_hp_landing_connected=False,actor_enemy_count_policy_connected=False,windows_actor_verified=False,audit_gpu_executions=0,canonical_world_admission=False,normal_ui='CPU',full_character_verified=0,full_goal_complete=False)
 (ROOT/'research/portable-world-actor-registry-validation.json').write_text(json.dumps(result,indent=2)+'\n')
 (ROOT/'research/portable-world-actor-registry-fingerprints.json').write_text(json.dumps(dict(scope=r['scope'],comparison=dict(input_sha256=sha(data),output_sha256=sha(raw),source_sha256=r['evidence']['source_sha256'],cases=fingerprints)),indent=2)+'\n');print('Actor registry242 sealed;initial237 and old208 full bytes preserved')
if __name__=='__main__':main()
