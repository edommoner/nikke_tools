"""Isolated single-receiver scheduling optimization, after all correctness gates.
The only normalized word is the actual high-water frame depth (header word 3).
It is retained separately and may decrease; every physics/history word must match.
"""
import argparse,array,copy,io,subprocess,tarfile,hashlib,importlib.util,json,shutil,statistics,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';sys.path[:0]=[str(R/'app'),str(R/'scripts')]
from portable_backend import execute,source_hashes
from portable_runtime import pack_programs,decode
from portable_specs import LIMITS as L

BASE='43f43a54535992d6992e0b3042c99c2e6c809bd4'
def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,r):(P/(n+'.json')).write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
def prepare(variant):
 folder=P/'portable-build'/('enemy-fanout-'+variant);folder.mkdir(parents=True,exist_ok=True)
 raw=subprocess.check_output(['git','archive',BASE,'gpu'],cwd=R)
 with tarfile.open(fileobj=io.BytesIO(raw)) as archive:archive.extractall(folder,filter='data')
 if variant=='single':
  path=folder/'gpu/event_runtime.slang';s=path.read_text()
  old='if(d.kind==0 && d.enemyBuff!=0 && recipientMask!=0 && f.mode!=19)'
  assert s.count(old)==1
  s=s.replace(old,'if(d.kind==0 && d.enemyBuff!=0 && recipientMask!=0 && f.mode!=19 && (countbits(recipientMask)!=1 || s.hpPendingMask!=0 || s.hpDirtyMask!=0))')
  old='            row = findCarrier(s,row,recipientMask,f.time,f.mode==19 ? f.repeatPassive : 0);'
  assert s.count(old)==1
  s=s.replace(old,'            uint capturedGeneration=d.enemyBuff!=0 && recipientMask!=0 ? (f.mode==19 ? f.repeatPassive : s.targetGeneration[firstbithigh(recipientMask>>5)]) : 0;\n            row = findCarrier(s,row,recipientMask,f.time,capturedGeneration);')
  old='if (d.enemyBuff != 0) s.enemyCaptureGeneration[row] = f.repeatPassive;';assert s.count(old)==1
  s=s.replace(old,'if (d.enemyBuff != 0) s.enemyCaptureGeneration[row] = capturedGeneration;')
  path.write_text(s,newline='\n')
 source=folder/('portable_enemy_fanout_'+variant+'.slang');source.write_text('#include "gpu/event_runtime.slang"\n',newline='\n')
 return source.relative_to(R).as_posix()

def run(source,programs):
 raw,evidence=execute(source,'portableEvents',pack_programs(programs),L['INPUT_WORDS'],L['OUTPUT_WORDS'],'metal')
 words=array.array('I');words.frombytes(raw)
 if sys.byteorder!='little':words.byteswap()
 depth=[]
 for i in range(len(programs)):
  base=i*L['OUTPUT_WORDS'];assert words[base]==0,(i,words[base]);depth.append(words[base+3]);words[base+3]=0
 if sys.byteorder!='little':words.byteswap()
 canonical=words.tobytes();return raw,canonical,depth,evidence

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--phase',required=True,choices=('parity','timing'));args=parser.parse_args()
 gates=load('portable-duration-extend-global-gates');order=load('portable-duration-extend-timing-order')
 assert gates['passed'] and gates['complete'] and order['passed'] and order['windows_execution_and_transfer_terminal'] and not order['verification_processes']
 live_source=source_hashes('gpu/event_runtime.slang')
 source_hash=json.loads(subprocess.check_output(['git','show',BASE+':research/portable-combat-metal.json'],cwd=R))['source_sha256']
 sp=importlib.util.spec_from_file_location('fanout_cases',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
 if args.phase=='parity':
  programs=[v.compile_case(c) for c in v.fixtures()];rows={};first=None;baseline_depth=None
  for variant in ('queued','single'):
   source=prepare(variant);raw,canonical,depth,evidence=run(source,programs)
   if first is None:first=canonical;baseline_depth=depth
   else:assert canonical==first and all(a<=b for a,b in zip(depth,baseline_depth))
   rows[variant]=dict(frame_high_water=depth,canonical_output_sha256=hashlib.sha256(canonical).hexdigest(),**evidence)
  assert source_hashes('gpu/event_runtime.slang')==live_source
  save('portable-enemy-fanout-parity',dict(passed=True,positive_inputs=len(programs),all_physics_and_history_words_equal=True,normalized_word='Header word 3 only, the true high-water frame depth; candidate never increases it',variants=rows,production_source_sha256=source_hash,timing_order=order))
  print('Enemy fanout normalized output parity passed',len(programs),flush=True);return
 parity=load('portable-enemy-fanout-parity');assert parity['passed'] and parity['production_source_sha256']==source_hash
 base=copy.deepcopy(next(c for c in v.fixtures() if c['name']=='duration-extend-enemy-independent-boss'))
 base['effects']=base['effects'][:1];base['effects'][0].update(duration=-1,max_stack=1,trigger=dict(timing=['on_attack'],condition=[]));base['owners']=[0]
 base['script']=[[0,4,0,0,0,-1,0,0]]+[[i/10,0,7,0,0,-1,0,0] for i in range(1,61)]+[[6,2,0,0,0,0,0,0]]
 results={}
 for workload,target in [('one-receiver','boss'),('three-receivers','all_enemies')]:
  case=copy.deepcopy(base);case['effects'][0]['target']=target
  program=v.compile_case(case);programs=[program]*256;rows={k:[] for k in ('queued','single')};expected=None
  for sample in range(4):
   for variant in ('queued','single'):
    raw,canonical,depth,evidence=run(prepare(variant),programs)
    sha=hashlib.sha256(canonical).hexdigest()
    if expected is None:expected=sha
    assert sha==expected
    words=array.array('I');words.frombytes(raw[:L['OUTPUT_WORDS']*4])
    if sys.byteorder!='little':words.byteswap()
    actual=decode(words,program[1]);assert actual['queries'][0]['enemy_modifiers']['defense_pct']==-20
    rows[variant].append(dict(warmup=sample==0,canonical_output_sha256=sha,frame_high_water=depth[0],**evidence));print(workload,sample,variant,evidence['transport']['gpu_seconds'],flush=True)
  medians={k:statistics.median(x['transport']['gpu_seconds'] for x in a[1:]) for k,a in rows.items()}
  results[workload]=dict(median_gpu_seconds=medians,single_to_queued_ratio=medians['single']/medians['queued'],samples=rows)
 assert source_hashes('gpu/event_runtime.slang')==live_source
 save('portable-enemy-fanout-benchmark',dict(passed=True,production_source_sha256=source_hash,workloads=results,timing_order=order,scope='Sequential isolated 256-program batches, 60 activations each; warmup then three samples; high-water depth is a diagnostic representation difference, every other output word identical; desktop GPU activity not excluded'))
 print('Enemy fanout benchmark complete',flush=True)
if __name__=='__main__':main()
