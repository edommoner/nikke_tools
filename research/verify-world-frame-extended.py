"""Beyond-command-count scheduling, MT rollover and fail-closed dynamic traces."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app')]
from portable_backend import execute,source_hashes
spec=importlib.util.spec_from_file_location('world_frame',ROOT/'research/verify-world-frame.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def fixtures():
 base=copy.deepcopy(f.fixtures()[0]);base['patterns'][0]['spec'].update(atk=1,target='random:3',hits=72,interval=1/60);base['duration']=1.3;base['name']='beyond64-72-attacks';rows=[base]
 c=copy.deepcopy(base);c['name']='same-frame-512-random3-mt-rollover';c['duration']=.05;c['patterns'][0]['spec'].update(hits=512,interval=0);rows.append(c)
 for name,target,hits,queries,records in [('target-query-capacity','slot:1',1025,1024,1024),('recipient-trace-capacity','all',411,410,2048)]:
  c=copy.deepcopy(base);c['name']=name;c['duration']=.05;c['effects']=[f.effect('invincible',target='all_allies')];c['owners']=[0];c['patterns'][0]['spec'].update(target=target,hits=hits,interval=0);c.update(expected_status=2,expected_queries=queries,expected_records=records);rows.append(c)
 c=copy.deepcopy(f.fixtures()[0]);c['name']='expiry-end-notice-before-target-selection';c['patterns'][0]['delay']=.2;c['patterns'][0]['spec'].update(target='top_atk:1',hits=1);c['effects']=[f.effect('crit_dmg',name='temp',duration=.1),f.effect('atk_pct',1000,trigger=dict(timing=['event:state_end:temp'],condition=[]))];c['owners']=[0,0];rows.append(c)
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--candidate',required=True,type=Path);p.add_argument('--backend',choices=['metal','cuda'],default='metal');p.add_argument('--names',nargs='+');p.add_argument('--report',type=Path);p.add_argument('--replay',type=Path);args=p.parse_args()
 candidate=args.candidate.resolve();prep=json.loads((candidate/'candidate-preparation.json').read_text());cases=fixtures()
 if args.names:
  wanted=set(args.names);cases=[c for c in cases if c['name'] in wanted];assert len(cases)==len(wanted),'Unknown selected case'
 compiled=[f.compile_case(c) for c in cases];data=array.array('I',[len(cases)])
 for words,_ in compiled:data.extend(words)
 if sys.byteorder!='little':data.byteswap()
 packed=data.tobytes()
 if args.replay:
  folder=args.replay.resolve();evidence=json.loads((folder/'evidence.json').read_text());raw=(folder/'readback.bin').read_bytes();assert packed==(folder/'input.bin').read_bytes() and hashlib.sha256(packed).hexdigest()==evidence['input_sha256'];assert hashlib.sha256(raw).hexdigest()==evidence['output_sha256'] and source_hashes(prep['source'])==evidence['source_sha256'] and evidence['backend']==args.backend
 else:
  folder=ROOT/'research/portable-build'/('world-frame-extended-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir();(folder/'input.bin').write_bytes(packed)
  raw,evidence=execute(prep['source'],'portableEvents',packed,88848,225280,args.backend);(folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 words=array.array('I');words.frombytes(raw)
 if sys.byteorder!='little':words.byteswap()
 rows=[]
 for index,(case,(_,meta)) in enumerate(zip(cases,compiled)):
  actual=None;native=None;block=words[index*225280:(index+1)*225280];status=case.get('expected_status',0)
  try:
   assert block[0]==status,('status',block[0],status);actual=f.read_result(block,meta,case);native=f.observe(case)
   if status==0:
    for key in ('damage','allies','covers','shots','ammo','hits','boss_log','rng','graph_states','graph_history'):assert actual[key]==native[key],key
    assert len(actual['target_queries'])==case['patterns'][0]['spec']['hits']
    if case['name'].startswith(('beyond64-','same-frame-')):assert len(actual['target_queries'])>64
    if 'rollover' in case['name']:assert actual['rng']['draws']>624 and len(actual['rng']['state'])==624 and len(actual['hits'])==1536
    if case['name']=='expiry-end-notice-before-target-selection':assert actual['hits'][0]['owner']==0 and actual['hits'][0]['time']>.1
   else:
    assert block[f.WF_OUTPUT+7]==case['expected_queries'] and block[f.WF_OUTPUT+6]==case['expected_records']
    assert len(actual['hits'])==case['expected_records'] and actual['hits']==native['hits'][:case['expected_records']]
  except Exception as error:rows.append(dict(name=case['name'],passed=False,error=repr(error),actual=actual,native=native))
  else:rows.append(dict(name=case['name'],passed=True,expected_status=status,actual=actual,native=native,scope='Full native fields' if status==0 else 'Explicit rejection and exact completed-recipient prefix only;not a successful full battle'))
 report=dict(passed=all(r['passed'] for r in rows),cases=rows,captured=str(folder),candidate=str(candidate),gpu_execution_reused=args.replay is not None,source_sha256_local={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('research/verify-world-frame.py','research/world_frame_native.py','research/verify-world-frame-extended.py')},cpu_scheduled_attacks_used_as_gpu_input=False,canonical_world_admission=False,windows_used=False,efficiency_started=False,full_character_verified=0,full_goal_complete=False,normal_ui='CPU',**evidence)
 report_path=ROOT/args.report if args.report else ROOT/f'research/portable-world-frame-extended-{args.backend}.json';report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert report['passed'],[(r['name'],r.get('error')) for r in rows if not r['passed']]
 print(len(rows),'extended frame cases verified',args.backend)
if __name__=='__main__':main()
