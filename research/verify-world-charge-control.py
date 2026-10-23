"""Common CUDA/Metal manual hold inputs versus full native battles."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','scripts','research')]
import engine_worker
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L,FIELDS as F
from portable_charge_control_specs import normalize_static_controls,compile_policy,OWNER_BASE,CLICK_BASE,SEQUENCE_BASE,THRESHOLD_BASE
from world_frame_native import roster_names,authored_metadata
from world_charge_control_native import observe as inspect_native
from world_charge_control_cases import fixtures
from calculator import timeline
s=importlib.util.spec_from_file_location('control_team_suite',ROOT/'research/verify-world-team.py');team=importlib.util.module_from_spec(s);s.loader.exec_module(team)
INPUT=L['WORLD_CONTROL_INPUT_WORDS'];OUTPUT=655360;SOURCE='gpu/world_charge_control_entry.slang'

def compile_case(case):
 if case.get('sequence'):raise ValueError('Squad focus sequences require common focus adapter')
 w,m,b=team.compile_case(case);names=roster_names(case);chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},control=copy.deepcopy(c)) for n,c in zip(names,case['controls'])]
 with patch.dict(timeline._NIKKE,authored_metadata(case)),patch.dict(timeline._DELAYS['_exceptions'],{},clear=True),patch.dict(timeline._DELAYS['_defaults_by_weapon_type'],{'AR':{'post_reload_delay':0}},clear=True):norm=normalize_static_controls(chars,case['base_atk'],case['enemy'],case['control_mode'])
 from portable_team_hit_specs import bound_effects
 effects=bound_effects([(e,names[o]) for e,o in zip(case['effects'],case['owners'])],m,names)
 policy=compile_policy(norm,effects,names,m['states'],w[L['WORLD_OVERLAY_INPUT_BASE']+1]);w[L['WORLD_OVERLAY_INPUT_BASE']+1]=policy[3];w.extend(policy);w[0]=L['WORLD_CONTROL_ABI'];w[L['TARGET_COUNTER_INPUT_BASE']+6]=21
 assert len(w)==INPUT;m['_control_policy']=policy;return w,m,b

def decoded(block,meta,case,bindings):
 r=team.decoded(block,meta,case,bindings);h=L['WORLD_CONTROL_HEAD_BASE'];assert block[h]==0x57434831 and block[h+1]<=220 and block[h+2]<=5 and block[h+3]<32 and not any(block[h+7:h+8]) and not any(block[h+9:h+10]) and not any(block[h+13:h+16])
 number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
 names={v:k for k,v in meta['states'].items()};notes=[];arbs=[];preempts=[0]*5
 for i in range(block[h+1]):
  at=L['WORLD_CONTROL_TRACE_BASE']+i*8;kind=block[at];who=block[at+1]
  if kind==0:
   assert who<=5 and block[at+4]<32 and block[at+5]<=5 and block[at+6]==block[at+7]==0
   if block[at+5]:preempts[block[at+5]-1]+=1
   arbs.append(dict(time=number(at+2),owner=who-1,camera_mask=block[at+4],preemptions=list(preempts)))
  else:
   assert kind==1 and who<5 and block[at+5]==0;notes.append(dict(owner=who,event=names[block[at+4]],time=number(at+2),full_time=number(at+6)))
 assert len(arbs)==block[h+8] and sum(preempts)==block[h+6]
 policy=meta['_control_policy'];chars=[]
 for who in range(5):
  at=L['WORLD_CONTROL_STATE_BASE']+who*32;owner=OWNER_BASE+who*8;fired=[]
  for i in range(policy[owner+2],policy[owner+2]+policy[owner+3]):
   if block[L['WORLD_CONTROL_FIRED_BASE']+i//32]&(1<<(i%32)):fired.append(names[policy[THRESHOLD_BASE+i*4+1]].removeprefix('charge_hold:'))
  assert block[at+24]<3 and block[at+1]<=8 and block[at+27]==preempts[who] and block[at+29]<=16
  chars.append(dict(owner=who,phase=('ready','charging','post_delay')[block[at+24]],full_time=number(at+2),release_time=None if number(at+6)==float('inf') else number(at+6),release_until_close=number(at+6)==float('inf'),sequence_index=block[at+1],fired=sorted(fired),reentry_anchors=sorted(number(L['WORLD_CONTROL_HISTORY_BASE']+who*32+i*2) for i in range(block[at+29]))))
 r['manual_control']=dict(notifications=notes,arbitration=arbs,characters=chars,owner=block[h+2]-1,camera_mask=block[h+3],owner_since=number(h+4),preemptions=preempts,burst_users=list(block[h+10:h+13]));return r

def prepare():
 allrows=fixtures();rows=[c for c in allrows if not c['name'].endswith('simultaneous-strict')];programs=[compile_case(c) for c in rows];strict=next(c for c in allrows if c['name'].endswith('simultaneous-strict'));bad=[('strict-control-collision',compile_case(strict)[0])];base=L['WORLD_CONTROL_INPUT_BASE'];seed=programs[0][0]
 changes=[('control-old-mode19',L['TARGET_COUNTER_INPUT_BASE']+6,19),('control-counter-marker',L['TARGET_COUNTER_INPUT_BASE'],0),('control-magic',base,0),('control-version',base+1,2),('control-mode3',base+2,3),('control-camera-conflict',base+3,1),('control-threshold-overflow',base+4,1281),('control-reserved',base+5,1),('control-click-overflow',base+OWNER_BASE,9),('control-sequence-overflow',base+OWNER_BASE+1,9),('control-threshold-offset',base+OWNER_BASE+2,1),('control-weapon-input-kind',base+OWNER_BASE+4,3),('control-unused-threshold',base+THRESHOLD_BASE+4,1),('control-negative-threshold',base+THRESHOLD_BASE+3,0xbff00000),('control-nan-threshold',base+THRESHOLD_BASE+3,0x7ff80000),('control-mismatched-threshold',base+THRESHOLD_BASE+3,0x3ff00000),('control-invalid-tag',base+THRESHOLD_BASE+1,256),('control-unassociated-tag',base+THRESHOLD_BASE+1,127),('control-missing-event-candidate',L['EVENT_CANDIDATE_BASE']+39*L['MASK_WORDS'],0),('control-event-nonfinite-seconds',L['EVENT_BASE']+6,0x7ff00000)]
 for name,at,value in changes:
  w=list(seed);w[at]=value;bad.append((name,w))
 lookup={c['name']:p[0] for c,p in zip(rows,programs)};seq=lookup['manual-charge-sequence-until-0.8'];click=lookup['manual-charge-own_full_burst-during_full_burst']
 for name,source,at,value in [('control-negative-sequence',seq,base+SEQUENCE_BASE+1,0xbff00000),('control-nan-release',seq,base+SEQUENCE_BASE+3,0x7ff80000),('control-tap-not-admitted',click,base+CLICK_BASE,1),('control-priority-overflow',click,base+CLICK_BASE+2,100),('control-invalid-window',click,base+CLICK_BASE+1,5),('control-down-charge-cannot-hold',seq,base+OWNER_BASE+4,2)]:
  w=list(source);w[at]=value;bad.append((name,w))
 return rows,programs,bad

def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('metal','cuda'),default='metal');ap.add_argument('--cpu-only',action='store_true');ap.add_argument('--replay',type=Path);a=ap.parse_args();rows,programs,bad=prepare();observed=[inspect_native(c) for c in rows]
 if a.cpu_only:print('Manual control native',len(rows),'reject',len(bad),'GPU0');return
 packed=array.array('I',[len(rows)+len(bad)])
 for w,_,_ in programs:packed.extend(w)
 for _,w in bad:packed.extend(w)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes();ow=OUTPUT*4
 if a.replay:
  folder=a.replay;assert (folder/'input.bin').read_bytes()==data;raw=(folder/'readback.bin').read_bytes();e=json.loads((folder/'evidence.json').read_text());assert e['source_sha256']==source_hashes(SOURCE)
 else:
  folder=ROOT/'research/portable-build'/('world-charge-control-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(data)
  try:raw,e=execute(SOURCE,'portableEvents',data,INPUT,OUTPUT,a.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
 checked=[]
 for i,(c,(_,m,b),(native,expected_trace)) in enumerate(zip(rows,programs,observed)):
  block=array.array('I');block.frombytes(raw[i*ow:(i+1)*ow])
  if sys.byteorder!='little':block.byteswap()
  try:
   actual=decoded(block,m,c,b);trace=team.skill_trace(block,m);changed=[k for k in native if k!='scope' and actual[k]!=native[k]]
   if trace!=expected_trace:changed.append('skill_trace')
  except Exception as error:actual=dict(error=repr(error));changed=['decode'];trace=[]
  checked.append(dict(name=c['name'],passed=block[0]==0 and not changed,status=block[0],changed=changed,actual=actual,native=native,skill_trace=trace,native_skill_trace=expected_trace))
 rejected=[dict(name=name,status=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little'),passed=int.from_bytes(raw[(len(rows)+i)*ow:(len(rows)+i)*ow+4],'little')==64) for i,(name,_) in enumerate(bad)]
 report=dict(passed=all(c['passed'] for c in checked+rejected),cases=checked,rejected_cases=rejected,captured=str(folder),evidence=e,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),unchanged_gpu_retries=0,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False)
 (ROOT/f'research/portable-world-charge-control-{a.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[(c['name'],c.get('changed'),c['status']) for c in checked+rejected if not c['passed']];print('Manual charge controls',len(rows),'native',len(bad),'reject',a.backend)
if __name__=='__main__':main()
