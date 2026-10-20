"""Shared world notice ordering, multiplicity, termination and raw rejection."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
spec=importlib.util.spec_from_file_location('frame',ROOT/'research/verify-world-frame.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
from calculator.boss_pattern import BOSS_EVENTS

def fixtures():
 base=copy.deepcopy(f.fixtures()[0]);base['duration']=.1;base['patterns'][0]['spec']['hits']=1;rows=[]
 for event in BOSS_EVENTS:
  c=copy.deepcopy(base);c['name']='later-node-notice-before-attack-'+event;c['effects']=[f.effect('invincible',target='all_allies',trigger=dict(timing=[event],condition=[]))];c['owners']=[0];c['patterns'].append(dict(id='b',kind='idle',emit=[event]));rows.append(c)
 for name,events in [('all-four-open-close',list(BOSS_EVENTS)),('duplicate-order',['event:target_spawn','event:part_destroy','event:target_spawn']),('maximum-eight',['event:target_spawn']*8)]:
  c=copy.deepcopy(base);c['name']=name;c['patterns'][0].update(emit=events,emit_end=list(reversed(events)),until=dict(time=.05));c['effects']=[f.effect('def_pct',10,target='all_allies',max_stack=32,trigger=dict(timing=list(BOSS_EVENTS),condition=[]))];rows.append(c)
 c=copy.deepcopy(base);c['name']='notice-after-expiry-tick';c['patterns'][0].update(delay=.05,emit=['event:part_destroy']);c['effects']=[f.effect('crit_dmg',1,name='temp',duration=.05),f.effect('invincible',target='all_allies',trigger=dict(timing=['event:part_destroy'],condition=['not_self_state:temp']))];c['owners']=[0,0];rows.append(c)
 c=copy.deepcopy(base);c['name']='notice-after-battle-start';c['patterns'][0]['emit']=['event:part_destroy'];c['effects']=[f.effect('invincible',target='all_allies',trigger=dict(timing=['event:part_destroy'],condition=['self_state:ready'])),f.effect('crit_dmg',1,name='ready')];c['owners']=[0,0];rows.append(c)
 c=copy.deepcopy(rows[0]);c['name']='close-notice-before-following-attack';c['patterns']=[dict(id='wait',kind='idle',until=dict(time=.05),emit_end=['event:part_destroy']),dict(c['patterns'][0],after=['wait'])];rows.append(c)
 c=copy.deepcopy(base);c['name']='finish-does-not-emit-end';c['patterns'][0]['emit_end']=list(BOSS_EVENTS);c['effects']=[f.effect('def_pct',100,target='all_allies',trigger=dict(timing=list(BOSS_EVENTS),condition=[]))];rows.append(c)
 c=copy.deepcopy(base);c['name']='spawn-notice-does-not-match-other-named-event';c['patterns'][0]['emit']=['event:target_spawn'];c['effects']=[f.effect('def_pct',100,target='all_allies',trigger=dict(timing=['event:unrelated'],condition=[]))];rows.append(c)
 c=copy.deepcopy(base);c['name']='sub-epsilon-notice-once';c['patterns'][0].update(until=dict(time=5e-10),emit=['event:target_spawn'],emit_end=['event:part_destroy']);c['effects']=[f.effect('def_pct',10,target='all_allies',max_stack=32,trigger=dict(timing=list(BOSS_EVENTS),condition=[]))];rows.append(c)
 c=copy.deepcopy(rows[-1]);c['name']='sub-epsilon-repeat-notice-once';c['patterns'][0].update(after=['start','a'],repeat=0);rows.append(c)
 return rows

def negative_inputs():
 base=copy.deepcopy(fixtures()[0]);words,_=f.compile_case(base);d=f.WF_INPUT+16+64;rows=[]
 for name,at,value in [('notice-count9',d+12,9),('notice-id0',d+14,0),('notice-id5',d+14,5),('notice-unused-bits',d+14,1|(1<<3)),('end-count-without-id',d+13,1),('spawn-tag-without-spawn',f.WF_INPUT+8,1),('unused-node-notice',d+2*64+12,1)]:
  w=list(words);w[at]=value;rows.append((name,w))
 base=copy.deepcopy(fixtures()[1]);words,_=f.compile_case(base)
 for name,value in [('spawn-tag-missing',0),('spawn-tag-over-capacity',257)]:
  w=list(words);w[f.WF_INPUT+8]=value;rows.append((name,w))
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=('metal','cuda'),default='metal');p.add_argument('--replay',type=Path);args=p.parse_args()
 cases=fixtures();compiled=[f.compile_case(c) for c in cases];negatives=negative_inputs();data=array.array('I',[len(cases)+len(negatives)])
 for words,_ in compiled:data.extend(words)
 for _,words in negatives:data.extend(words)
 if sys.byteorder!='little':data.byteswap()
 packed=data.tobytes();source='gpu/world_frame_entry.slang'
 if args.replay:
  folder=args.replay.resolve();evidence=json.loads((folder/'evidence.json').read_text());raw=(folder/'readback.bin').read_bytes();assert (folder/'input.bin').read_bytes()==packed and evidence['source_sha256']==source_hashes(source) and hashlib.sha256(raw).hexdigest()==evidence['output_sha256'] and evidence['backend']==args.backend
 else:
  folder=ROOT/'research/portable-build'/('world-notices-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(packed)
  raw,evidence=execute(source,'portableEvents',packed,f.L['WORLD_FRAME_INPUT_WORDS'],f.L['WORLD_FRAME_OUTPUT_WORDS'],args.backend);(folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 stride=f.L['WORLD_FRAME_OUTPUT_WORDS'];rows=[];keys=('damage','allies','covers','shots','ammo','hits','boss_log','rng','graph_states','graph_history')
 for i,(case,(_,meta)) in enumerate(zip(cases,compiled)):
  block=values[i*stride:(i+1)*stride];actual=f.read_result(block,meta,case);native=f.observe(case);diffs=[k for k in keys if actual[k]!=native[k]];notices=[]
  for j in range(block[f.WF_OUTPUT+2]):
   at=f.WF_OUTPUT+2832+j*6;kind,node,outcome=block[at:at+3]
   if kind not in (1,2):continue
   expected=0 if kind==2 and outcome==4 else len(case['patterns'][node].get('emit' if kind==1 else 'emit_end',[]))
   notices.append(dict(kind=kind,node=node,outcome=outcome,actual=block[at+5],expected=expected));
  if not all(n['actual']==n['expected'] for n in notices):diffs.append('notice-delivery-counts')
  if case['name'].startswith(('later-node-','notice-after-','close-notice-')) and any(h['hp']!=0 for h in native['hits']):diffs.append('native-order-witness-did-not-protect')
  rows.append(dict(name=case['name'],passed=block[0]==0 and not diffs,differences=diffs,notice_records=notices,actual=actual,native=native))
 rejected=[dict(name=name,status=values[(len(cases)+i)*stride],passed=values[(len(cases)+i)*stride]==64) for i,(name,_) in enumerate(negatives)]
 report=dict(passed=all(r['passed'] for r in rows+rejected),cases=rows,rejected_cases=rejected,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),gpu_execution_reused=args.replay is not None,canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,normal_ui='CPU',scope='Four closed pattern emit/emit_end events,all notices before attacks,after tick/battle_start,duplicates,expiry,repeat,finish suppression. Full native fields and GPU delivery counts. Same source/fixtures for CUDA and Metal.')
 (ROOT/f'research/portable-world-notices-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert report['passed'],[(r['name'],r.get('differences',r.get('status'))) for r in rows+rejected if not r['passed']]
 print(len(rows),'notice cases and',len(rejected),'raw rejections passed',args.backend)
if __name__=='__main__':main()
