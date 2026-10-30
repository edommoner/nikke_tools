"""Common GPU body versus complete native simulations for overlay providers.
Gates/actors are deliberately rejected until their corresponding hooks exist.
"""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
from portable_specs import LIMITS as L
from portable_world_schedule_specs import compile_schedule
from portable_world_overlay_specs import compile_payload
from world_frame_native import observe,authored_metadata,roster_names

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
f=module('overlay_body_frame','research/verify-world-frame.py')
n=module('overlay_body_native','research/characterize-world-overlays.py')
SOURCE='gpu/world_overlay_entry.slang'

def cases():
 rows=[case for case in n.simulation_cases() if case['name'] not in ('native-overlay-vanish','native-overlay-shield')]
 base=copy.deepcopy(rows[0]);c=copy.deepcopy(base);c['name']='world-and-character-received-insertion-order'
 c['patterns']=[dict(id='world-first',kind='buff',enemy=dict(received_dmg_pct=-1e16)),dict(id='world-later',kind='buff',delay=.1,enemy=dict(received_dmg_pct=1))]
 c['effects']=[f.effect('received_dmg_pct',1e16,target='all_enemies')];c['owners']=[0];rows.append(c)
 c=copy.deepcopy(base);c['name']='reversed-declaration-opening-order';c['patterns']=[dict(id='a',kind='buff',delay=.2,enemy=dict(def_mult=2,def_add=1)),dict(id='b',kind='buff',enemy=dict(def_mult=3,def_add=4))];rows.append(c)
 c=copy.deepcopy(base);c['name']='negative-defense-intermediate';c['patterns']=[dict(id='a',kind='buff',enemy=dict(def_mult=0,def_add=-10)),dict(id='b',kind='buff',enemy=dict(def_mult=2,def_add=30))];rows.append(c)
 c=copy.deepcopy(base);c['name']='core-condition-at-battle-start';c['patterns']=[dict(id='core',kind='core',core_px=52)];c['effects']=[f.effect('atk_pct',20,trigger=dict(timing=['battle_start'],condition=['core_hit']))];rows.append(c)
 return rows

def compile_case(case,*,actor_pools=False):
 from calculator.boss_pattern import BossScript
 from portable_geometry_specs import validate
 names=roster_names(case);enemy=case['enemy'];auth=copy.deepcopy(case);auth['effects']=[__import__('portable_world_overlay_specs').compiler_effect(e) for e in auth['effects']];auth['combat']['targets'][0]['defense']=enemy.get('def',0)
 geometry=dict(core_px=enemy.get('core_px',0),distance=enemy.get('distance'),optimal_weapons=enemy.get('optimal_range_weapons',[]),weapons=[dict(type=w.get('base_weapon_type','MG' if w.get('mode')=='auto_warmup' else 'AR'),minimum=10,maximum=20) for w in case['combat']['weapons']])
 validate(geometry);auth['environment']['geometry']=geometry
 literal=case.get('literal_weapon_geometry')
 if literal is not None and (not isinstance(literal,list) or len(literal)!=5 or any(set(w)!={'spread_start','spread_end','spread_shots'} for w in literal)):raise ValueError('Invalid literal weapon geometry')
 for who,weapon in enumerate(auth['combat']['weapons']):weapon.update(**(literal[who] if literal is not None else dict(spread_start=20,spread_end=10,spread_shots=5)),core_diameter=geometry['core_px'])
 graph,patterns=compile_schedule(dict(patterns=case['patterns'],clock='accumulated',duration=case['duration']),notice_payload=True)
 BossScript(patterns,copy.deepcopy(enemy),lambda *_:False) # Same cross-domain constraints as native.
 payload=None
 auth['patterns']=[{k:v for k,v in p.items() if k not in ('enemy','irremovable','core_px','weapons','distance')} if p['kind'] in ('idle','groggy','attack') else dict({k:v for k,v in p.items() if k in ('id','after','delay','until','repeat','emit','emit_end')},kind='idle') for p in case['patterns']]
 if actor_pools:
  from calculator.boss_pattern import BOSS_EVENTS
  target_spawn=any('event:target_spawn' in (*p.emit,*p.emit_end,*(e for x in p.targets for e in x.emits)) for p in patterns)
  auth['patterns']=[dict(id=p.id,kind='idle') for p in patterns]
  if target_spawn:auth['patterns'][0]['emit']=['event:target_spawn']
 if case.get('observe_overlay'):
  from unittest.mock import patch
  with patch.dict(f.engine_worker.META,authored_metadata(case)),patch.object(f,'NAMES',names):words,meta=f.compile_case(auth)
 else:words,meta=f.compile_case(auth)
 from portable_world_overlay_specs import CODES
 shield=any(p.kind=='shield' for p in patterns)
 elements=case.get('element_codes') or [case.get('weapon_metadata',{}).get('element_code',f.engine_worker.META[name].get('element_code','')) for name in names]
 tags={p.code:meta['states'][p.code]+1 for p in patterns if p.kind=='shield' and p.code in meta['states'] and words[L['WORLD_META_BASE']+1]!=0}
 payload=compile_payload(patterns,camera_mask=sum(1<<i for i,name in enumerate(names) if name in case.get('camera',[])),element_codes=[CODES.get(code,0) for code in elements] if shield else (),code_tags=tags,named_refs={e['target_effect']:meta['states'][e['target_effect']]+1 for e in case['effects'] if e.get('stat')=='received_dmg_buff_mag_pct'},charge_hold_mask=sum(1<<i for i,name in enumerate(names) if name=='스노우 화이트 : 헤비암즈'),actor_pools=actor_pools)
 if actor_pools and target_spawn:graph[8]=meta['states']['target_spawn']+1
 words[L['WORLD_FRAME_INPUT_BASE']:L['WORLD_FRAME_PAYLOAD_BASE']]=graph;words[0]=L['WORLD_OVERLAY_ABI'];words.extend(payload)
 if actor_pools:
  from portable_world_attack_specs import pack_attacks
  pack_attacks(words,patterns,case['patterns'],L)
 from portable_world_overlay_specs import pack_cleanse_flags,pack_skill_mode_flags
 pack_cleanse_flags(words,case['effects'],L);pack_skill_mode_flags(words,case['effects'],L)
 assert len(words)==L['WORLD_OVERLAY_INPUT_WORDS'];return words,meta

from portable_world_result import read_overlay_result

def negative_inputs(programs):
 from portable_world_schedule_specs import number
 buff=list(programs[1][0]);core=list(programs[3][0]);header=L['WORLD_OVERLAY_INPUT_BASE'];node=L['WORLD_OVERLAY_NODE_BASE']+16
 edits=[('bad-magic',buff,header,0x574f3032),('reserved-header',buff,header+7,1),('unsupported-shield',buff,node,5),('unsupported-vanish',buff,node,6),('invalid-buff-flags',buff,node+1,2),('reserved-node',buff,node+15,1),('unused-node',buff,L['WORLD_OVERLAY_NODE_BASE']+31*16,1),('disabled-nonzero-payload',buff,header,0)]
 rows=[]
 for name,original,at,value in edits:
  words=list(original);words[at]=value;rows.append((name,words))
 words=list(buff);words[node:node+16]=[4]+[0]*9+[64]+[0]*5;rows.append(('mask-overflow',words))
 for name,original,offset,value in [('negative-multiplier',buff,2,-1),('nan-buff',buff,4,float('nan')),('infinite-received',buff,6,float('inf')),('zero-core',core,8,0),('negative-core',core,8,-1),('fractional-core',core,8,.5),('oversized-core',core,8,100000001)]:
  words=list(original);words[node+offset:node+offset+2]=number(value);rows.append((name,words))
 words=list(buff);words[header+1]=32;rows.append(('camera-mask-overflow',words))
 words=list(buff);words[header+2]=6;rows.append(('roster-code-outside-closed-domain',words))
 for name,tag,code in [('shield-code-zero',0,0),('shield-code-six',0,6),('shield-tag-outside-namespace',1,2)]:
  words=list(buff);words[node:node+16]=[5]+[0]*7+[tag,0,code]+[0]*5;rows.append((name,words))
 words=list(buff);words[node:node+16]=[6]+[0]*7+[1]+[0]*7;rows.append(('vanish-nonzero-payload',words))
 words=list(buff);words[L['LANDING_META_BASE']]=0;rows.append(('world-overlay-requires-native-landing',words))
 words=list(buff);words[header+8]=1;rows.append(('cleanse-flag-on-non-cleanse-definition',words))
 words=list(buff);words[header+15]=1<<31;rows.append(('cleanse-flag-outside-definition-count',words))
 if len(programs)>35:
  cleanse=list(programs[35][0]);at=L['DEFINITION_BASE']
  assert cleanse[at+1]==26 and cleanse[header+8]&1
  words=list(cleanse);words[at+6:at+8]=number(float('nan'));rows.append(('cleanse-nonfinite-count',words))
  words=list(cleanse);words[at+21]=3;rows.append(('cleanse-invalid-recipient-domain',words))
 if len(programs)>70:
  mode=list(programs[70][0]);at=L['MODE_BASE']+31;assert mode[L['DEFINITION_BASE']+1]==2
  words=list(mode);words[at]=2;rows.append(('weapon-mode-policy-nonboolean',words))
  words=list(buff);words[at]=1;rows.append(('weapon-mode-policy-on-nonmode-definition',words))
  words=list(mode);words[L['MODE_BASE']+255*L['MODE_WORDS']+31]=1;rows.append(('weapon-mode-policy-outside-definition-count',words))
  words=list(mode);words[at]=1;words[header:header+528]=[0]*528;rows.append(('weapon-mode-policy-with-disabled-overlay',words))
 if len(programs)>99:
  for name,value in [('hold-policy-empty-mask',0x48410000),('hold-policy-owner-overflow',0x48410020),('hold-policy-unknown-tag',0x48420001)]:
   words=list(buff);words[header+7]=value;rows.append((name,words))
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=('metal','cuda'),default='metal');p.add_argument('--replay',type=Path);p.add_argument('--gates',action='store_true');p.add_argument('--reuse',type=Path);p.add_argument('--cleanse',action='store_true');p.add_argument('--skill-modes',action='store_true');p.add_argument('--charge-hold',action='store_true');args=p.parse_args();rows=cases();
 if args.gates or args.cleanse or args.skill_modes or args.charge_hold:rows+=module('overlay_gates','research/world_overlay_gate_cases.py').fixtures()
 if args.cleanse or args.skill_modes or args.charge_hold:rows+=module('overlay_cleanse','research/world_overlay_cleanse_cases.py').fixtures()
 if args.skill_modes or args.charge_hold:rows+=module('overlay_skill_modes','research/world_overlay_skill_mode_cases.py').fixtures()
 if args.charge_hold:rows+=module('overlay_charge_hold','research/world_overlay_charge_hold_cases.py').fixtures()
 programs=[compile_case(c) for c in rows]
 negative=negative_inputs(programs);suite=module('overlay_previous_suite','research/verify-world-suite.py');prior=suite.cases();golden=json.loads(suite.GOLDEN.read_text());assert len(prior)==len(golden['cases'])==49
 packed=array.array('I',[len(rows)+len(negative)+len(prior)])
 for words,_ in programs:packed.extend(words)
 for _,words in negative:packed.extend(words)
 for (name,words),expected in zip(prior,golden['cases']):
  block=array.array('I',words)
  if sys.byteorder!='little':block.byteswap()
  assert name==expected['name'] and hashlib.sha256(block.tobytes()).hexdigest()==expected['input_sha256']
  upgraded=list(words);upgraded[0]=L['WORLD_OVERLAY_ABI'];upgraded.extend([0]*528);packed.extend(upgraded)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if args.replay:
  folder=args.replay.resolve();raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert (folder/'input.bin').read_bytes()==data and evidence['source_sha256']==source_hashes(SOURCE) and hashlib.sha256(raw).hexdigest()==evidence['output_sha256'] and evidence['backend']==args.backend
 elif args.reuse:
  previous=args.reuse.resolve();old_input=(previous/'input.bin').read_bytes();old_raw=(previous/'readback.bin').read_bytes();old_evidence=json.loads((previous/'evidence.json').read_text())
  assert old_evidence['source_sha256']==source_hashes(SOURCE) and old_evidence['backend']==args.backend
  assert hashlib.sha256(old_input).hexdigest()==old_evidence['input_sha256'] and hashlib.sha256(old_raw).hexdigest()==old_evidence['output_sha256']
  assert len(old_input)==len(data) and old_input[:4]==data[:4]
  count=int.from_bytes(data[:4],'little');iw=L['WORLD_OVERLAY_INPUT_WORDS']*4;ow=L['WORLD_FRAME_OUTPUT_WORDS']*4
  assert len(old_raw)==count*ow
  changed=[i for i in range(count) if data[4+i*iw:4+(i+1)*iw]!=old_input[4+i*iw:4+(i+1)*iw]]
  assert 0<len(changed)<count,changed
  dispatch_data=struct.pack('<I',len(changed))+b''.join(data[4+i*iw:4+(i+1)*iw] for i in changed)
  folder=ROOT/'research/portable-build'/('world-overlay-incremental-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data);(folder/'dispatch-input.bin').write_bytes(dispatch_data)
  fresh,fresh_evidence=execute(SOURCE,'portableEvents',dispatch_data,L['WORLD_OVERLAY_INPUT_WORDS'],L['WORLD_FRAME_OUTPUT_WORDS'],args.backend)
  (folder/'dispatch-readback.bin').write_bytes(fresh);(folder/'dispatch-evidence.json').write_text(json.dumps(fresh_evidence,indent=2)+'\n')
  assert fresh_evidence['source_sha256']==old_evidence['source_sha256'] and fresh_evidence['generated_sha256']==old_evidence['generated_sha256']
  assembled=bytearray(old_raw)
  for j,i in enumerate(changed):assembled[i*ow:(i+1)*ow]=fresh[j*ow:(j+1)*ow]
  raw=bytes(assembled)
  evidence=dict(backend=args.backend,gpu_execution_verified=True,source_sha256=fresh_evidence['source_sha256'],generated_sha256=fresh_evidence['generated_sha256'],input_sha256=hashlib.sha256(data).hexdigest(),output_sha256=hashlib.sha256(raw).hexdigest(),transport=dict(backend=args.backend,cases=count,command_status='completed',composed=True,source_identical=True,reused_inputs=count-len(changed),fresh_inputs=len(changed)),execution_composition=dict(prior_capture=str(previous),prior_input_sha256=old_evidence['input_sha256'],prior_output_sha256=old_evidence['output_sha256'],fresh_dispatch_evidence='dispatch-evidence.json',fresh_input_sha256=fresh_evidence['input_sha256'],fresh_output_sha256=fresh_evidence['output_sha256'],changed_indices=changed,physical_gpu_sessions_this_invocation=1,scope='Only identical source and byte-identical per-case inputs reuse prior GPU readbacks;all changed inputs execute on the GPU once.No CPU output substitution.'))
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 else:
  folder=ROOT/'research/portable-build'/('world-overlay-body-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,L['WORLD_OVERLAY_INPUT_WORDS'],L['WORLD_FRAME_OUTPUT_WORDS'],args.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,(case,(_,meta)) in enumerate(zip(rows,programs)):
  actual=read_overlay_result(values[i*L['WORLD_FRAME_OUTPUT_WORDS']:(i+1)*L['WORLD_FRAME_OUTPUT_WORDS']],meta,case);native=observe(case)
  if case.get('observe_overlay'):
   block=values[i*L['WORLD_FRAME_OUTPUT_WORDS']:(i+1)*L['WORLD_FRAME_OUTPUT_WORDS']];head=L['WORLD_OVERLAY_STATE_BASE'];number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
   from world_overlay_node_readback import read_nodes
   actual.update(gauge=actual['ordinary']['queries'][-1]['combat']['gauge'],world_nodes=read_nodes(block,len(case['patterns']),cleanse=case.get('observe_cleanse',False)))
  if case.get('observe_charge_hold'):
   weapons=actual['ordinary']['queries'][-1]['combat']['weapons']
   charge=L['WORLD_OVERLAY_CHARGE_BASE']
   actual['charge_hold']=[dict(owner=i,charging=weapons[i]['charging'],full_time=number(charge+i*8+6) if block[charge+i*8]&1 else -1.,deadline=number(charge+i*8+4) if block[charge+i*8]&2 else -1.) for i,name in enumerate(roster_names(case)) if name=='스노우 화이트 : 헤비암즈']
  changed=[k for k in ('damage','allies','covers','shots','ammo','hits','boss_log','rng','graph_states','graph_history') if actual[k]!=native[k]]
  if case.get('observe_overlay'):changed += [k for k in ('gauge','world_nodes') if actual[k]!=native[k]]
  if case.get('observe_charge_hold'):changed += [k for k in ('charge_hold',) if actual[k]!=native[k]]
  results.append(dict(name=case['name'],passed=actual['status']==0 and not changed,changed=changed,actual=actual,native=native))
 rejected=[dict(name=name,status=values[(len(rows)+i)*L['WORLD_FRAME_OUTPUT_WORDS']],passed=values[(len(rows)+i)*L['WORLD_FRAME_OUTPUT_WORDS']]==64) for i,(name,_) in enumerate(negative)]
 preserved=[]
 for i,expected in enumerate(golden['cases']):
  offset=(len(rows)+len(negative)+i)*L['WORLD_FRAME_OUTPUT_WORDS']*4;block=raw[offset:offset+L['WORLD_FRAME_OUTPUT_WORDS']*4];digest=hashlib.sha256(block).hexdigest();preserved.append(dict(name=expected['name'],passed=digest==expected['output_sha256'],output_sha256=digest,expected_sha256=expected['output_sha256']))
 report=dict(passed=all(r['passed'] for r in results+rejected+preserved),preserved_world49=preserved,rejected_cases=rejected,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),cases=results,captured=str(folder),evidence=evidence,gpu_execution_composed=bool(evidence.get('execution_composition')),scope='Shared executor frame->ordered overlay snapshot->defense/core/range/ordered boss+character enemy effects versus complete native simulate;gates are opt-in fixture coverage;skill_damage is an opt-in private ABI75 fixture only;actors remain closed;cleanse is an explicit experimental definition flag',full_character_verified=0,canonical_world_admission=False,full_goal_complete=False)
 (ROOT/f'research/portable-world-overlay-{"charge-hold" if args.charge_hold else "skill-modes" if args.skill_modes else "cleanse" if args.cleanse else "gates" if args.gates else "body"}-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[(r['name'],r.get('changed'),r.get('status',r.get('actual',{}).get('status'))) for r in results+rejected+preserved if not r['passed']]
 print(len(rows),'world overlay body cases match complete native simulate;',len(rejected),'raw descriptors rejected;49 old outputs preserved',args.backend)
if __name__=='__main__':main()
