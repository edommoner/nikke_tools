"""Actual full-native reload programs through one shared CUDA/Metal executable."""
import argparse,array,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
from portable_reload_specs import pack as pack_reload
from portable_team_hit_specs import bound_effects
from world_reload_cases import fixtures
from world_reload_native import observe as inspect_native
from world_frame_native import roster_names
s=importlib.util.spec_from_file_location('reload_charge_suite',ROOT/'research/verify-world-charge-control.py');charge=importlib.util.module_from_spec(s);s.loader.exec_module(charge)
INPUT=L['WORLD_RELOAD_INPUT_WORDS'];OUTPUT=L['WORLD_RELOAD_OUTPUT_WORDS'];SOURCE='gpu/world_reload_entry.slang'

def compile_case(case):
 w,m,b=charge.compile_case(case);names=roster_names(case);effects=bound_effects([(e,names[o]) for e,o in zip(case['effects'],case['owners'])],m,names)
 w.extend(pack_reload(e for e,owner in effects));w[0]=L['WORLD_RELOAD_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=22
 assert len(w)==INPUT;return w,m,b

def decoded(block,meta,case,bindings):
 r=charge.decoded(block,meta,case,bindings);h=L['WORLD_RELOAD_HEAD_BASE'];assert block[h]==0x57524c31 and block[h+1]<=L['WORLD_RELOAD_TRACE_COUNT'] and not any(block[h+2:h+4]) and not any(block[h+14:h+16])
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0];names={v:k for k,v in meta['states'].items()};events=[]
 for i in range(block[h+1]):
  at=L['WORLD_RELOAD_TRACE_BASE']+i*16;kind,who=block[at:at+2];assert kind<3 and who<5 and not any(block[at+12:at+16])
  if kind==0:
   assert not any(block[at+5:at+12]);events.append(dict(kind='force',owner=who,time=number(at+2),name=names[block[at+4]]))
  else:
   assert block[at+7]<3;ammo=block[at+6];events.append(dict(kind=('start','finish')[kind-1],owner=who,time=number(at+2),until=number(at+4),ammo=ammo if ammo<0x80000000 else ammo-0x100000000,phase=('ready','charging','post_delay')[block[at+7]],full_time=number(at+8),release_time=number(at+10)))
 r['reload_events']=events;r['reload_until']=[number(h+4+who*2) for who in range(5)];return r

def prepare():
 rows=fixtures();programs=[compile_case(c) for c in rows];bad=[];p=L['WORLD_RELOAD_INPUT_BASE'];seed=programs[0][0];f=L['DEFINITION_BASE'];force=f+L['DEFINITION_WORDS']
 changes=[('old-abi',0,L['WORLD_CONTROL_ABI']),('old-mode21',L['TARGET_COUNTER_INPUT_BASE']+6,21),('reload-magic',p,0),('reload-version',p+1,2),('reload-count',p+2,3),('reload-reserved',p+3,1),('reload-unused-flags',p+10,1),('reload-unknown-flags',p+8,4),('reload-fixed-force-flag',p+8,2),('reload-force-missing-flag',p+9,0),('reload-force-fixed-flag',p+9,1),('reload-fixed-kind',f+F['KIND'],4),('reload-fixed-stat',f+F['STAT'],91),('reload-force-stat',force+F['STAT'],1),('reload-force-kind',force+F['KIND'],0),('reload-fixed-nan',f+F['VALUE']+1,0x7ff80000),('reload-force-infinite',force+F['VALUE']+1,0x7ff00000),('reload-force-enemy-recipient',L['RECIPIENT_BASE']+8,4),('reload-control-marker',L['WORLD_CONTROL_INPUT_BASE'],0)]
 for name,at,value in changes:
  w=list(seed);w[at]=value;bad.append((name,w))
 return rows,programs,bad

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows,programs,bad=prepare();observed=[inspect_native(c) for c in rows]
 if a.cpu_only:print('Reload native',len(rows),'reject',len(bad),'GPU0');return
 packed=array.array('I',[len(rows)+len(bad)])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes();ow=OUTPUT*4
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();e=json.loads((folder/'evidence.json').read_text());assert e['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-reload-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,e=execute(SOURCE,'portableEvents',data,INPUT,OUTPUT,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
 checked=[]
 for i,(c,(_,m,b),(native,expected_trace)) in enumerate(zip(rows,programs,observed)):
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  try:
   actual=decoded(block,m,c,b);trace=charge.team.skill_trace(block,m);changed=[k for k in native if k!='scope' and actual[k]!=native[k]]
   if trace!=expected_trace:changed.append('skill_trace')
  except Exception as error:actual=dict(error=repr(error));changed=['decode'];trace=[]
  checked.append(dict(name=c['name'],passed=block[0]==0 and not changed,status=block[0],changed=changed,actual=actual,native=native,skill_trace=trace,native_skill_trace=expected_trace))
 rejected=[dict(name=name,status=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little'),passed=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little')==64) for i,(name,_) in enumerate(bad)]
 report=dict(passed=all(c['passed'] for c in checked+rejected),cases=checked,rejected_cases=rejected,captured=str(folder),evidence=e,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),unchanged_gpu_retries=0,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-reload-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[(c['name'],c.get('changed'),c['status']) for c in checked+rejected if not c['passed']];print('Reload common',len(rows),'native',len(bad),'reject',a.backend)
if __name__=='__main__':main()
