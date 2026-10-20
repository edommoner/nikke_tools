"""Shared GPU graph scheduler versus actual native BossScript, not a schedule replay."""
import argparse,array,copy,datetime,hashlib,json,math,random,struct,sys,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
import engine_worker
from portable_backend import execute,source_hashes
from portable_world_schedule_specs import compile_schedule,INPUT_WORDS,OUTPUT_WORDS,NODE_BASE,FRAME_BASE
from world_schedule_native import observe

def attack(name='a',**kw):return dict(id=name,kind='attack',spec=dict(coeff=100,target='all',hits=4,interval=.1),**kw)
def fixture(name,patterns,frames=None,**kw):
 row=dict(name=name,patterns=patterns,**kw)
 if frames is not None:row['frames']=frames
 return row
def fixtures():
 rows=[]
 for interval in (0,.1,1/60,5e-324):
  due=interval-1e-9
  times=sorted(set([0,math.nextafter(max(0,due),-math.inf),max(0,due),math.nextafter(max(0,due),math.inf),interval,.2,.5]))
  times=[t for t in times if t>=0]
  p=attack();p['spec']['interval']=interval
  rows.append(fixture('pending-multiply-'+str(interval),[p],[[t,0] for t in times]))
 for duration in (.1,1/60,1.0,5e-324):
  p=attack(until={'time':duration});p['spec']['interval']=duration
  boundary=max(0,duration-1e-9);times=sorted(set([0,math.nextafter(boundary,-math.inf),boundary,math.nextafter(boundary,math.inf),duration,duration+1]))
  rows.append(fixture('expire-before-same-frame-shot-'+str(duration),[p],[[t,0] for t in times if t>=0]))
 for reverse in (False,True):
  pats=[attack('a'),attack('b')];pats=pats[::-1] if reverse else pats
  rows.append(fixture('declaration-order-'+str(reverse),pats,[[0,0],[0,0],[.35,0],[1,0]]))
 chain=[dict(id=f'p{i}',kind='idle',until={'time':1} if i==31 else {'time':30,'after':[{'node':f'p{i+1}'}]}) for i in range(32)]
 rows.append(fixture('reverse-following-chain32',chain,[[0,0],[1,0],[2,0]]))
 for repeat in (1,2,3,0):
  p=attack(after=['start','a'],repeat=repeat,until={'time':.2})
  rows.append(fixture('self-repeat-'+str(repeat),[p],[[i/10,0] for i in range(16)]))
 cycle=[dict(id='a',kind='idle',after=['start','c'],repeat=0,until={'time':.2}),dict(id='b',kind='idle',after=['a'],repeat=0,until={'time':.1}),dict(id='c',kind='idle',after=['b'],repeat=0,until={'time':.1})]
 for clock in ('accumulated','rational'):rows.append(fixture('cycle-'+clock,cycle,clock=clock,duration=2))
 for reverse in (False,True):
  a=dict(id='a',kind='idle',after=['start','a'],repeat=0,until={'time':.1})
  b=dict(id='b',kind='idle',after=['start','b'],repeat=0,until={'time':.15})
  c=attack('c',after=['b','a'] if reverse else ['a','b'],repeat=0,until={'time':.25})
  rows.append(fixture('consumes-all-edge-backlog-'+str(reverse),[a,b,c],[[t,0] for t in [0,.1,.2,.3,.5,.75,1,1.5,2]]))
 for cleared in (False,True):
  pats=[dict(id='p',kind='parts',targets=[dict(name='part',hp=10)],until={'targets_cleared':True,'time':1,'after':[{'node':'x'}]}),dict(id='x',kind='idle',until={'time':1})]
  for outcome in ('cleared','expired','followed'):
   # Expired is a valid authored branch even when followed wins this execution.
   pats2=copy.deepcopy(pats)+[dict(id='child',kind='idle',after=[dict(node='p',outcome=outcome)])]
   rows.append(fixture('reason-priority-'+str(cleared)+'-'+outcome,pats2,[[0,0],[1,int(cleared)],[2,0]]))
 rows.append(fixture('late-start-anchor',[attack(delay=.5)],[[5,0],[5,0],[5.5,0],[6,0]]))
 rows.append(fixture('large-finite-overflow',[attack(until={'time':1e308})],[[1e308,0],[1e308,0]],duration=1e308))
 rows.append(fixture('source-delay-overflow',[dict(id='a',kind='idle',until={'time':1}),dict(id='b',kind='idle',after=['a'],delay=1e308)],[[0,0],[1,0],[1e308,0]],duration=1e308))
 for hits in (1,5,1000):
  p=attack();p['spec'].update(hits=hits,interval=0);rows.append(fixture('same-frame-hits-'+str(hits),[p],[[0,0],[1,0]]))
 kinds=[('idle',{}),('groggy',{}),('buff',dict(enemy=dict(def_mult=2))),('core',dict(core_px=10)),('parts',dict(targets=[dict(name='part',hp=10)])),('interrupt',dict(targets=[dict(name='circle',hp=10)])),('shield',dict(code='작열')),('vanish',{}),('move',dict(weapons=['AR'])),('attack',dict(spec=dict(coeff=100,target='all',hits=3,interval=.1))),('debuff',dict(spec=dict(target='all',debuffs=[dict(stat='atk_pct',value=-10)],hits=3,interval=.1))),('summon',dict(spec=dict(hp=10,count=2)))]
 for kind,payload in kinds:
  rows.append(fixture('kind-graph-'+kind,[dict(id='node',kind=kind,until={'time':.5},**payload),dict(id='child',kind='idle',after=['node'])],[[0,0],[.2,0],[.5,0],[1,0]]))
 for clock in ('accumulated','rational'):
  rows.append(fixture('180-second-'+clock,[attack(delay=179,until={'time':1})],clock=clock,duration=180))
  rows.append(fixture('history-capacity-'+clock,[dict(id='a',kind='idle',after=['start','a'],repeat=0,until={'time':1/60})],clock=clock,duration=15,status=2))
 rng=random.Random(701)
 for index in range(40):
  pats=[]
  for n in range(rng.randrange(2,9)):
   after=['start'] if n==0 else [rng.choice(['start',*[p['id'] for p in pats]])]
   until={'time':rng.choice([.05,.1,.2,.3,.5])}
   if n>0 and rng.random()<.5:until['after']=[dict(node=rng.choice(pats)['id'],delay=rng.choice([0,.05,.15]))]
   p=attack(f'n{n}',after=after,delay=rng.choice([0,.03,.1]),until=until);p['spec'].update(hits=rng.randrange(1,10),interval=rng.choice([0,.01,.05,.1]));pats.append(p)
  rows.append(fixture('mixed-graph-'+str(index),pats,[[i/20,0] for i in range(61)]))
 return rows

def negative_cases(base):
 words,_=compile_schedule(base);rows=[]
 def add(name,word,value):
  v=list(words);v[word]=value;rows.append((name,v))
 for name,word,value in [('magic',0,0),('zero-nodes',1,0),('33-nodes',1,33),('65-frames',2,65),('bad-clock',3,3),('bad-finish',4,2),('header-reserved',5,1),('header-tail',15,1),('empty-after',NODE_BASE+10,0),('9-after',NODE_BASE+10,9),('9-until',NODE_BASE+11,9),('flags',NODE_BASE+1,4),('node-reserved',NODE_BASE+7,1),('node-tail',NODE_BASE+63,1),('unknown-node',NODE_BASE+16,33),('start-filter',NODE_BASE+17,1),('unused-edge',NODE_BASE+18,1),('unused-node',NODE_BASE+64,1),('frame-reserved',FRAME_BASE+3,1),('clear-without-rule',FRAME_BASE+2,1),('unused-frame',FRAME_BASE+63*4,1)]:add(name,word,value)
 v=list(words);v[NODE_BASE+2:NODE_BASE+4]=list(struct.unpack('<II',struct.pack('<d',float('nan'))));rows.append(('nan-delay',v))
 return rows

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=['metal','cuda'],default='metal');parser.add_argument('--native-only',action='store_true');parser.add_argument('--replay',type=Path);args=parser.parse_args()
 if args.native_only and args.replay:raise ValueError('Native-only and retained GPU replay are separate modes')
 cases=fixtures();compiled=[];native=[]
 for case in cases:
  words,patterns=compile_schedule(case);compiled.append(words);native.append(observe(case,patterns))
 # Independent witnesses guard the native observer/projection, not just parity.
 witness={c['name']:n for c,n in zip(cases,native)}
 assert [r[1] for r in witness['declaration-order-False']['log'] if r[0]==3 and r[3:5]==[0,0]]==[0,1]
 assert [r[1] for r in witness['reverse-following-chain32']['history'][1:33]]==[3]*31+[2]
 assert witness['expire-before-same-frame-shot-0.1']['states'][0][4]==1
 assert next(r for r in witness['reason-priority-True-cleared']['history'] if r[0]==0)[1]==1
 assert next(r for r in witness['reason-priority-False-followed']['history'] if r[0]==0)[1]==3
 negatives=negative_cases(cases[0]);all_words=[*compiled,*[w for _,w in negatives]];packed=array.array('I',[len(all_words)])
 for words in all_words:packed.extend(words)
 if sys.byteorder!='little':packed.byteswap()
 folder=None;evidence={};raw=None
 if not args.native_only:
  data=packed.tobytes()
  if args.replay:
   folder=args.replay.resolve();evidence=json.loads((folder/'evidence.json').read_text());raw=(folder/'readback.bin').read_bytes()
   assert (folder/'input.bin').read_bytes()==data and hashlib.sha256(data).hexdigest()==evidence['input_sha256']
   assert hashlib.sha256(raw).hexdigest()==evidence['output_sha256'] and evidence['source_sha256']==source_hashes('gpu/world_schedule_probe.slang')
   assert evidence['gpu_execution_verified'] and evidence['backend']==args.backend and len(raw)==len(all_words)*OUTPUT_WORDS*4
  else:
   folder=ROOT/'research/portable-build'/('world-schedule-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
   (folder/'input.bin').write_bytes(data)
   raw,evidence=execute('gpu/world_schedule_probe.slang','worldScheduleProbe',data,INPUT_WORDS,OUTPUT_WORDS,args.backend)
   (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
  gpu=array.array('I');gpu.frombytes(raw)
  if sys.byteorder!='little':gpu.byteswap()
 rows=[]
 for i,(case,expected) in enumerate(zip(cases,native)):
  actual=None
  try:
   status=case.get('status',0)
   if raw is not None:
    block=gpu[i*OUTPUT_WORDS:(i+1)*OUTPUT_WORDS];assert block[0]==status,('status',block[0],status)
    hc,lc,sc,fc=block[1:5]
    actual=dict(states=[list(block[16+n*24:16+(n+1)*24]) for n in range(32)],history=[list(block[784+n*4:784+(n+1)*4]) for n in range(hc)],log=[list(block[2832+n*6:2832+(n+1)*6]) for n in range(lc)],snapshots=[[list(block[15120+f*768+n*24:15120+f*768+(n+1)*24]) for n in range(32)] for f in range(sc)],frames=fc)
    if status==0:
     for key in actual:assert actual[key]==expected[key],key
    else:
     assert hc==512 and lc==1023 and actual['history']==expected['history'][:hc] and actual['log']==expected['log'][:lc],'Bounded failure must preserve native trace prefix'
  except Exception as error:rows.append(dict(name=case['name'],passed=False,error=repr(error),native=expected,actual=actual))
  else:
   compact={k:v for k,v in expected.items() if k!='snapshots'}
   compact['snapshot_sha256']=[hashlib.sha256(struct.pack('<768I',*(word for row in snapshot for word in row))).hexdigest() for snapshot in expected['snapshots']]
   compact['snapshot_words_per_frame']=768
   # All full states/snapshots were compared above. Raw GPU blocks are retained;
   # successful duplicate projections are omitted only after exact equality.
   rows.append(dict(name=case['name'],passed=True,expected_status=case.get('status',0),native=compact,actual=actual if case.get('status',0)!=0 else None,full_gpu_projection_equals_native=raw is not None and case.get('status',0)==0,snapshot_count=len(expected['snapshots'])))
 rejected=[]
 for offset,(name,_) in enumerate(negatives):
  status=gpu[(len(cases)+offset)*OUTPUT_WORDS] if raw is not None else None
  rejected.append(dict(name=name,status=status,checked=raw is not None,passed=status==64 if raw is not None else None))
 report=dict(passed=all(r['passed'] for r in rows) and (all(r['passed'] for r in rejected) if raw is not None else True),cases=rows,rejected_cases=rejected,captured=str(folder) if folder else None,gpu_execution_reused=args.replay is not None,successful_duplicate_projections_removed_after_full_comparison=raw is not None,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),base_compute_commit='73570451569dce424667e37f4729e475ea6b0a86',source_sha256_local={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('gpu/world_schedule.slang','gpu/world_schedule_probe.slang','app/portable_world_schedule_specs.py','research/world_schedule_native.py','research/verify-world-schedule.py','tests/test_portable_world_schedule.py','research/upstream/nikke-calc-master/calculator/boss_pattern.py')},native_schedules_used_as_gpu_input=False,normal_ui='CPU',canonical_world_admission=False,full_character_verified=0,full_goal_complete=False,scope='Shared scheduler component:full graph state,ends,ordered open/close/fire ledger and per-authored-frame snapshots versus native BossScript. GPU clock180s included. Cleared masks are authored component stimuli,not CPU-computed world state. Actor/overlay/effect payloads,summon shots and canonical runtime hookup remain incomplete.',**evidence)
 suffix='native' if args.native_only else args.backend
 (ROOT/f'research/portable-world-schedule-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert report['passed'],[(r['name'],r.get('error')) for r in rows+rejected if not r['passed']]
 print(len(rows),'shared scheduler graphs passed',suffix,('; '+str(len(rejected))+' raw GPU rejections passed' if raw is not None else '; raw GPU rejections pending'))
if __name__=='__main__':main()
