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
from world_frame_native import observe

def module(name,path):
 spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
f=module('overlay_body_frame','research/verify-world-frame.py')
n=module('overlay_body_native','research/characterize-world-overlays.py')
SOURCE='gpu/world_overlay_entry.slang'

def cases():
 rows=[r['case'] for r in n.full_simulations() if r['name'] not in ('native-overlay-vanish','native-overlay-shield')]
 base=copy.deepcopy(rows[0]);c=copy.deepcopy(base);c['name']='world-and-character-received-insertion-order'
 c['patterns']=[dict(id='world-first',kind='buff',enemy=dict(received_dmg_pct=-1e16)),dict(id='world-later',kind='buff',delay=.1,enemy=dict(received_dmg_pct=1))]
 c['effects']=[f.effect('received_dmg_pct',1e16,target='all_enemies')];c['owners']=[0];rows.append(c)
 c=copy.deepcopy(base);c['name']='reversed-declaration-opening-order';c['patterns']=[dict(id='a',kind='buff',delay=.2,enemy=dict(def_mult=2,def_add=1)),dict(id='b',kind='buff',enemy=dict(def_mult=3,def_add=4))];rows.append(c)
 c=copy.deepcopy(base);c['name']='negative-defense-intermediate';c['patterns']=[dict(id='a',kind='buff',enemy=dict(def_mult=0,def_add=-10)),dict(id='b',kind='buff',enemy=dict(def_mult=2,def_add=30))];rows.append(c)
 c=copy.deepcopy(base);c['name']='core-condition-at-battle-start';c['patterns']=[dict(id='core',kind='core',core_px=52)];c['effects']=[f.effect('atk_pct',20,trigger=dict(timing=['battle_start'],condition=['core_hit']))];rows.append(c)
 return rows

def compile_case(case):
 from calculator.boss_pattern import BossScript
 from portable_geometry_specs import validate
 enemy=case['enemy'];auth=copy.deepcopy(case);auth['combat']['targets'][0]['defense']=enemy.get('def',0)
 geometry=dict(core_px=enemy.get('core_px',0),distance=enemy.get('distance'),optimal_weapons=enemy.get('optimal_range_weapons',[]),weapons=[dict(type='AR',minimum=10,maximum=20) for _ in range(5)])
 validate(geometry);auth['environment']['geometry']=geometry
 for weapon in auth['combat']['weapons']:weapon.update(spread_start=20,spread_end=10,spread_shots=5,core_diameter=geometry['core_px'])
 graph,patterns=compile_schedule(dict(patterns=case['patterns'],clock='accumulated',duration=case['duration']),notice_payload=True)
 BossScript(patterns,copy.deepcopy(enemy),lambda *_:False) # Same cross-domain constraints as native.
 payload=compile_payload(patterns)
 auth['patterns']=[{k:v for k,v in p.items() if k not in ('enemy','irremovable','core_px','weapons','distance')} if p['kind'] in ('idle','groggy','attack') else dict({k:v for k,v in p.items() if k in ('id','after','delay','until','repeat','emit','emit_end')},kind='idle') for p in case['patterns']]
 words,meta=f.compile_case(auth);words[L['WORLD_FRAME_INPUT_BASE']:L['WORLD_FRAME_PAYLOAD_BASE']]=graph;words[0]=L['WORLD_OVERLAY_ABI'];words.extend(payload)
 assert len(words)==L['WORLD_OVERLAY_INPUT_WORDS'];return words,meta

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=('metal','cuda'),default='metal');p.add_argument('--replay',type=Path);args=p.parse_args();rows=cases();programs=[compile_case(c) for c in rows]
 packed=array.array('I',[len(rows)])
 for words,_ in programs:packed.extend(words)
 if sys.byteorder!='little':packed.byteswap()
 data=packed.tobytes()
 if args.replay:
  folder=args.replay.resolve();raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text());assert (folder/'input.bin').read_bytes()==data and evidence['source_sha256']==source_hashes(SOURCE) and hashlib.sha256(raw).hexdigest()==evidence['output_sha256'] and evidence['backend']==args.backend
 else:
  folder=ROOT/'research/portable-build'/('world-overlay-body-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(data)
  try:raw,evidence=execute(SOURCE,'portableEvents',data,L['WORLD_OVERLAY_INPUT_WORDS'],L['WORLD_FRAME_OUTPUT_WORDS'],args.backend)
  except Exception as error:(folder/'failure.json').write_text(json.dumps(dict(error=repr(error),source_sha256=source_hashes(SOURCE)),indent=2)+'\n');raise
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 results=[]
 for i,(case,(_,meta)) in enumerate(zip(rows,programs)):
  actual=f.read_result(values[i*L['WORLD_FRAME_OUTPUT_WORDS']:(i+1)*L['WORLD_FRAME_OUTPUT_WORDS']],meta,case);native=observe(case)
  changed=[k for k in ('damage','allies','covers','shots','ammo','hits','boss_log','rng','graph_states','graph_history') if actual[k]!=native[k]]
  results.append(dict(name=case['name'],passed=actual['status']==0 and not changed,changed=changed,actual=actual,native=native))
 report=dict(passed=all(r['passed'] for r in results),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),cases=results,captured=str(folder),evidence=evidence,scope='Shared executor frame->ordered overlay snapshot->defense/core/range/ordered boss+character enemy effects versus complete native simulate;gates/cleanse/actors still closed',full_character_verified=0,canonical_world_admission=False,full_goal_complete=False)
 (ROOT/f'research/portable-world-overlay-body-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');assert report['passed'],[(r['name'],r['changed'],r['actual']['status']) for r in results if not r['passed']]
 print(len(rows),'world overlay body cases match complete native simulate',args.backend)
if __name__=='__main__':main()
