"""Drive an isolated common executor with GPU-scheduled incoming boss attacks."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
import engine_worker
from world_authored_roster import skill_levels
from portable_backend import execute,source_hashes
from portable_runtime import compile_program,decode
from portable_specs import LIMITS as L
from portable_world_schedule_specs import compile_schedule,number
from portable_enemy_target_specs import target_rule
from timer_registry_cases import NAMES
from world_frame_native import observe
WF_INPUT=L['WORLD_FRAME_INPUT_BASE'];WF_PAYLOAD=L['WORLD_FRAME_PAYLOAD_BASE'];WF_OUTPUT=L['WORLD_FRAME_OUTPUT_BASE'];WF_TARGETS=L['WORLD_FRAME_TARGET_BASE'];WF_HITS=L['WORLD_FRAME_HIT_BASE']
def effect(stat,value=0,**kw):
 return dict(name=kw.pop('name',stat or 'noop'),source='스킬1',type='buff',stat=stat,fixed_value=value,target=kw.pop('target','self'),duration=kw.pop('duration',-1),trigger=kw.pop('trigger',dict(timing=['battle_start'],condition=[])),**kw)
def fixtures():
 rows=[]
 base=dict(name='initial-zero-before-own-shot',duration=.5,patterns=[dict(id='a',kind='attack',spec=dict(coeff=100,atk=100,target='all',hits=3,interval=.1))],effects=[effect('')],owners=[0],base_atk=[1000,1100,1200,1300,1400],combat=dict(clock='accumulated',weapons=[dict(enabled=True,stage=0,gauge=0,capacity=1000,interval=1,reload=1) for _ in NAMES],targets=[dict(hp=1e30,defense=0)]),environment=dict(allies=[dict(base_hp=1000,base_defense=10*i,base_cover_hp=1000) for i in range(5)],native_landing=True,cover_sync=True))
 rows.append(base)
 for rule in ('slot:2','top_atk:2','random:2'):
  for owner in (0,4):
   c=copy.deepcopy(base);c['name']=f'taunt-{rule}-{owner}';c['patterns'][0]['spec']['target']=rule;c['effects']=[effect('taunt')];c['owners']=[owner];rows.append(c)
 for stat,value in [('shield_from_max_hp_pct',30),('decoy',50),('received_dmg_split_even',0),('invincible',0)]:
  c=copy.deepcopy(base);c['name']='layer-'+stat;c['effects']=[effect(stat,value,target='all_allies')];c['patterns'][0]['spec'].update(target='slot:3',hits=4,interval=.1,atk=200);rows.append(c)
 c=copy.deepcopy(base);c['name']='lethal-before-own-zero-shot';c['patterns'][0]['spec'].update(atk=2000,target='slot:1',hits=1);rows.append(c)
 c=copy.deepcopy(base);c['name']='automatic-reload-cover';c['duration']=1;c['combat']['weapons']=[dict(enabled=True,stage=0,gauge=0,capacity=2,interval=.1,reload=.2) for _ in NAMES];c['patterns'][0]['spec'].update(hits=8,interval=.1,atk=100);rows.append(c)
 c=copy.deepcopy(base);c['name']='received-hit-buff-next-attacker-order';c['effects']=[effect('def_pct',50,target='all_allies',trigger=dict(timing=['received_hit'],condition=[]))];c['owners']=[0];c['patterns'][0]['spec'].update(target='slot:1',hits=1);c['patterns'].append(dict(id='b',kind='attack',spec=dict(coeff=100,atk=100,target='all',hits=1)));rows.append(c)
 c=copy.deepcopy(base);c['name']='expiry-cancels-pending';c['patterns'][0]['until']={'time':.1};rows.append(c)
 c=copy.deepcopy(base);c['name']='cyclic-frame-attacks';c['duration']=1;c['patterns'][0].update(after=['start','a'],repeat=0,until={'time':.2});c['patterns'][0]['spec'].update(target='random:1',hits=2,interval=.1);rows.append(c)
 c=copy.deepcopy(base);c['name']='rank-before-exact-expiry-boundary';c['patterns'][0]['delay']=.2;c['patterns'][0]['spec'].update(target='top_atk:1',hits=1);c['effects']=[effect('atk_pct',1000,duration=.2)];rows.append(c)
 return rows
def compile_case(case):
 for p in case['patterns']:
  if p['kind'] not in ('idle','groggy','attack') or p.get('until',{}).get('targets_cleared') or p.get('spec',{}).get('debuffs'):raise ValueError('World payload is not connected at this frame-coupling stage')
 duration=case['duration'];clock='accumulated' if case['combat'].get('clock')=='accumulated' else 'rational'
 graph,patterns=compile_schedule(dict(patterns=case['patterns'],clock=clock,duration=duration),notice_payload=True)
 chars=[dict(name=n,skill_levels=level,_weapon=dict(engine_worker.META[n],reload_time=case['combat']['weapons'][i]['reload'])) for i,(n,level) in enumerate(zip(NAMES,skill_levels(case)))]
 script=[[duration,24,0,0,0,-1,0,0],[duration,30,0,0,0,-1,0,0],[duration,2,0,0,-1,0,0,0]]
 words,meta=compile_program(chars,[(e,NAMES[o]) for e,o in zip(case['effects'],case['owners'])],script,case['base_atk'],combat=case['combat'],world_frame=True,world_notice_names=('target_spawn',) if any('event:target_spawn' in (*p.emit,*p.emit_end) for p in patterns) else (),**case['environment'])
 assert len(words)==86016;words[0]=L['WORLD_FRAME_ABI'];words.extend(graph);words.extend([0]*512)
 words[L['ENEMY_TARGET_META_BASE']:L['ENEMY_TARGET_META_BASE']+8]=[1,0,0,0,0,0,0,0]
 meta['enemy_targeting']=dict(enabled=True,steps=[],seed=0)
 if any('event:target_spawn' in (*p.emit,*p.emit_end) for p in patterns):words[WF_INPUT+8]=meta['states']['target_spawn']+1
 from portable_world_attack_specs import pack_attacks
 pack_attacks(words,patterns,case['patterns'],L)
 assert len(words)==L['WORLD_FRAME_INPUT_WORDS']
 return words,meta
from portable_world_result import read_result,order_squad_logs

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['metal','cuda'],default='metal');p.add_argument('--replay',type=Path);args=p.parse_args()
 cases=fixtures();compiled=[compile_case(c) for c in cases];packed=array.array('I',[len(cases)])
 for words,_ in compiled:packed.extend(words)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if args.replay:
  folder=args.replay.resolve();prep=json.loads((folder/'candidate-preparation.json').read_text());evidence=json.loads((folder/'evidence.json').read_text());raw=(folder/'readback.bin').read_bytes();assert data==(folder/'input.bin').read_bytes();assert evidence['source_sha256']==source_hashes(prep['source']) and hashlib.sha256(raw).hexdigest()==evidence['output_sha256'] and evidence['backend']==args.backend
 else:
  spec=importlib.util.spec_from_file_location('world_frame_prepare',ROOT/'research/prepare-world-frame-candidate.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);prep=module.prepare();folder=Path(prep['created']);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(prep['source'],'portableEvents',data,L['WORLD_FRAME_INPUT_WORDS'],L['WORLD_FRAME_OUTPUT_WORDS'],args.backend)
  except Exception as error:
   (folder/'execution-failure.json').write_text(json.dumps(dict(passed=False,error=repr(error),prepared=prep),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 rows=[]
 for i,(case,(_,meta)) in enumerate(zip(cases,compiled)):
  actual=None;native=None
  try:
   actual=read_result(values[i*L['WORLD_FRAME_OUTPUT_WORDS']:(i+1)*L['WORLD_FRAME_OUTPUT_WORDS']],meta,case);assert actual['status']==0,actual['status'];native=observe(case)
   for key in ('damage','allies','covers','shots','ammo','hits','boss_log','rng','graph_states','graph_history'):assert actual[key]==native[key],key
   if case['name']=='lethal-before-own-zero-shot':assert actual['shots'][0]==0 and actual['allies'][0]['down']
   if case['name']=='expiry-cancels-pending':assert len(actual['hits'])==5
   if case['name']=='automatic-reload-cover':assert any(h['cover']>0 for h in actual['hits'])
   if case['name']=='rank-before-exact-expiry-boundary':assert actual['hits'][0]['owner']==0 and actual['hits'][0]['time']<.2
   if case['name']=='received-hit-buff-next-attacker-order':assert next(h for h in actual['hits'] if h['pattern']=='b' and h['owner']==1)['damage']==85
  except Exception as error:rows.append(dict(name=case['name'],passed=False,error=repr(error),actual=actual,native=native))
  else:rows.append(dict(name=case['name'],passed=True,actual=actual,native=native))
 report=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),source_sha256_local={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('research/prepare-world-frame-candidate.py','research/verify-world-frame.py','research/world_frame_native.py','gpu/world_frame_addresses.slang','gpu/world_frame_runtime.slang','tests/test_portable_world_frame_input.py')},passed=all(r['passed'] for r in rows),cases=rows,captured=str(folder),prepared=prep,gpu_execution_reused=args.replay is not None,cpu_attack_schedule_used_as_gpu_input=False,canonical_world_admission=False,windows_used=False,efficiency_started=False,normal_ui='CPU',full_character_verified=0,full_goal_complete=False,scope='Canonical shared frame->graph->native-order victim/protection/split/HP coupling versus complete native simulate;direct attack/idle/groggy and closed pattern notices only.No overlays/debuff/actor/control/revive admission yet.',**evidence)
 (ROOT/f'research/portable-world-frame-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert report['passed'],[(r['name'],r.get('error')) for r in rows if not r['passed']]
 print(len(rows),'GPU-scheduled frame/attack cases match full native simulate',args.backend)
if __name__=='__main__':main()
