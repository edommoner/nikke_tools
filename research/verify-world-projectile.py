"""Shared CUDA/Metal physical projectile numbers versus full native simulation."""
import argparse,array,datetime,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
from portable_projectile_specs import ABI,MODE,HEAD,TRACE,TRACE_COUNT,finalize_program
from world_projectile_cases import fixtures
from world_projectile_native import observe as inspect_native
s=importlib.util.spec_from_file_location('projectile_reload','research/verify-world-reload.py');reload=importlib.util.module_from_spec(s);s.loader.exec_module(reload)
SOURCE='gpu/world_projectile_entry.slang';INPUT=104400;OUTPUT=786432

def compile_case(c):
 w,m,b=reload.compile_case(c);finalize_program(w);return w,m,b

def decoded(block,meta,case,bindings):
 r=reload.decoded(block,meta,case,bindings);head=HEAD;assert block[head]==0x57505231 and block[head+1]<=TRACE_COUNT and block[head+2]==0 and block[head+3]<=1 and not any(block[head+4:head+16]);events=[]
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 for i in range(block[head+1]):
  at=TRACE+i*16;assert block[at]<5 and block[at+1]<3 and block[at+7]==0 and not any(block[at+10:at+16])
  events.append(dict(owner=block[at],mode=block[at+1],time=number(at+2),pellets=block[at+4],muzzles=block[at+5],reach=block[at+6],damage=number(at+8)))
 r['projectile_shots']=events;return r

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];seed=programs[0][0];bad=[]
 for name,at,value in [('old-roster-abi',0,0x5045568c),('old-roster-mode',L['TARGET_COUNTER_INPUT_BASE']+6,23),('projectile-kind',L['DEFINITION_BASE']+F['KIND'],4),('projectile-nan',L['DEFINITION_BASE']+F['VALUE']+1,0x7ff80000),('projectile-no-combat',3,0)]:
  w=list(seed);w[at]=value;bad.append((name,w))
 for name,value in [('pellet-cap-overflow',4097),('positive-huge-pellet-count',1e200)]:
  w=list(seed);pos=L['DEFINITION_BASE']+F['VALUE'];w[pos:pos+2]=list(struct.unpack('<II',struct.pack('<d',value)));bad.append((name,w))
 for name,kind,key,arg in [('resource-key-overflow',18,256,0),('resource-mod-zero',21,0,0),('resource-mod-fractional',21,0,2.5)]:
  w=list(seed);w[L['RESOURCE_META_BASE']]=1;w[L['DEFINITION_BASE']+F['CONDITION_COUNT']]=1;at=L['CONDITION_BASE'];w[at:at+4]=[kind,key,*struct.unpack('<II',struct.pack('<d',arg))];bad.append((name,w))
 return rows,programs,bad

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows,programs,bad=prepare();observed=[inspect_native(c) for c in rows]
 if a.cpu_only:
  (ROOT/'research/portable-world-projectile-native-contract.json').write_text(json.dumps(dict(cases=[dict(name=c['name'],native=n,skill_trace=t) for c,(n,t) in zip(rows,observed)],gpu_calls=0,canonical_reference_modified=False),ensure_ascii=False,indent=2)+'\n');print('Projectile native',len(rows),'reject',len(bad),'GPU0');return
 packed=array.array('I',[len(rows)+len(bad)])
 for w,m,b in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes();ow=OUTPUT*4
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();e=json.loads((folder/'evidence.json').read_text());assert e['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-projectile-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,e=execute(SOURCE,'portableEvents',data,INPUT,OUTPUT,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
 checked=[]
 for i,(c,(_,m,b),(native,expected_trace)) in enumerate(zip(rows,programs,observed)):
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow]);block.byteswap() if sys.byteorder!='little' else None
  try:
   actual=decoded(block,m,c,b);trace=reload.charge.team.skill_trace(block,m);changed=[k for k in native if k!='scope' and actual[k]!=native[k]]
   if trace!=expected_trace:changed.append('skill_trace')
  except Exception as error:actual=dict(error=repr(error));changed=['decode'];trace=[]
  checked.append(dict(name=c['name'],passed=block[0]==0 and not changed,status=block[0],changed=changed,actual=actual,native=native,skill_trace=trace,native_skill_trace=expected_trace))
 rejected=[dict(name=name,status=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little'),passed=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little')==64) for i,(name,_) in enumerate(bad)]
 report=dict(passed=all(c['passed'] for c in checked+rejected),cases=checked,rejected_cases=rejected,captured=str(folder),evidence=e,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),unchanged_gpu_retries=0,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-projectile-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print([(c['name'],c['status'],c.get('changed')) for c in checked+rejected if not c['passed']]);assert report['passed'];print('Projectile common',len(rows),'native',len(bad),'reject',a.backend)
if __name__=='__main__':main()
