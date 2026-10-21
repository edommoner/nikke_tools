"""Eleven newly packable real profiles; complete effects, two battle durations."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import engine_worker
from detail_coverage import body_for
from portable_backend import execute,source_hashes
from portable_runtime import decode
from portable_projectile_roster_input import compile_projectile_battle,SOURCE,INPUT_WORDS,OUTPUT_WORDS
from portable_projectile_specs import HEAD,TRACE,TRACE_COUNT
from world_projectile_native import capture_projectile_shots
from world_real_binding_proof import binding_view
s=importlib.util.spec_from_file_location('projectile_roster_oracle',ROOT/'scripts/verify-portable-real-battle.py');reference=importlib.util.module_from_spec(s);s.loader.exec_module(reference)
s=importlib.util.spec_from_file_location('projectile_roster_policy',ROOT/'research/audit-world-roster-input.py');policy=importlib.util.module_from_spec(s);s.loader.exec_module(policy)
PROFILES=[('네온 : 비전 아이',0),('베스티',0),('라플라스',0),('라플라스',1),('라플라스',2),('라플라스',3),('도로시 : 세렌디피티',0),('레오나',0),('아르카나 : 포츈 메이트',0),('파워',0),('A2',0)]

def prepare():
 rows=[]
 for name,stage in PROFILES:
  for duration in (3,30):
   b=dict(body_for(policy.roster_for(name),duration),burst_gauge_mode='accumulate');b['profile']['chars'][name]['favorite_stage']=stage
   if stage:b['profile']['chars'][name]['collection_stage']='SR15'
   p=engine_worker.evaluate(dict(b,_portable_static_inputs=True));w,m=compile_projectile_battle(p);rows.append((dict(character=name,favorite_stage=stage,duration=duration,body=b),p,w,m))
 return rows

def native_reference(body):
 with capture_projectile_shots(body['squad']) as shots:r=reference.native_reference(body)
 return r,shots

def trace(block):
 assert block[HEAD]==0x57505231 and block[HEAD+1]<=TRACE_COUNT and block[HEAD+3]<=1 and not any(block[HEAD+4:HEAD+16]);rows=[]
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for i in range(block[HEAD+1]):
  at=TRACE+i*16;assert block[at]<5 and block[at+1]<3 and block[at+7]==0 and not any(block[at+10:at+16])
  rows.append(dict(owner=block[at],mode=block[at+1],time=number(at+2),pellets=block[at+4],muzzles=block[at+5],reach=block[at+6],damage=number(at+8)))
 return rows,block[HEAD+2]

def compare(block,prepared,program,native,shots):
 w,m=program;actual=decode(block[:159744],m);p,cpu=binding_view(prepared,native,m)
 diff=reference.compare_native_result(actual,p,cpu,program=program);events,omitted=trace(block)
 diff+=reference.differences(events,shots[:TRACE_COUNT],'physical_shots')
 if len(shots)-len(events)!=omitted:diff.append(dict(path='physical_history_omitted',gpu=omitted,cpu=len(shots)-len(events)))
 return actual,events,omitted,diff

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows=prepare();packed=array.array('I',[len(rows)])
 for c,p,w,m in rows:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if a.cpu_only:
  for c,p,w,m in rows:native_reference(c['body'])
  print('Complete real',len(rows),'battles;GPU0');return
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();e=json.loads((folder/'evidence.json').read_text());assert e['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-projectile-rosters-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,e=execute(SOURCE,'portableEvents',data,INPUT_WORDS,OUTPUT_WORDS,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
 results=[];ow=OUTPUT_WORDS*4
 for i,(c,p,w,m) in enumerate(rows):
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow]);block.byteswap() if sys.byteorder!='little' else None
  row=dict(**c,status=block[0],passed=False,prepared_effects=len(p['effects']),bound_effects=len(m['effects']))
  try:
   native,shots=native_reference(c['body']);actual,events,omitted,diff=compare(block,p,(w,m),native,shots);row.update(actual=actual,native=native,physical_shots=events,native_physical_shots=shots,physical_history_omitted=omitted,differences=diff,passed=block[0]==0 and not diff)
  except (AssertionError,ValueError,KeyError,IndexError) as error:row['error']=repr(error)
  results.append(row)
 report=dict(passed=all(r['passed'] for r in results),cases=results,evidence=e,captured=str(folder),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),full_character_verified=0,canonical_world_admission=False,normal_ui='CPU',full_goal_complete=False,cpu_trace_used_as_gpu_input=False,unchanged_gpu_retries=0,scope='Eleven complete real base/favorite profiles at3/30s, all definitions and physical shot snapshots; not full catalog/variants/world/control certification')
 (ROOT/f'research/portable-world-projectile-rosters-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print([(r['character'],r['favorite_stage'],r['duration'],r['status'],len(r.get('differences',[])),r.get('error')) for r in results]);assert report['passed']
if __name__=='__main__':main()
