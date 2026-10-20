"""Post-verification isolated enemy-target scalar filters; retain every input/readback before assertions."""
import array,copy,datetime,hashlib,importlib.util,io,json,statistics,struct,subprocess,sys,tarfile
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';SOURCE='782a13ca6249a52c30003b88870420cbd5b2f7ee'
sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime as rt
from portable_specs import ABI,LIMITS as L

def load(n):return json.loads((P/(n+'.json')).read_text())
def save(n,x):(P/(n+'.json')).write_text(json.dumps(x,indent=2)+'\n')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
def read_input(path):
 a=array.array('I');a.frombytes(Path(path).read_bytes())
 if sys.byteorder!='little':a.byteswap()
 count=a[0];assert len(a)==1+count*L['INPUT_WORDS']
 return [(list(a[1+i*L['INPUT_WORDS']:1+(i+1)*L['INPUT_WORDS']]),{}) for i in range(count)]
def write_input(path,items):
 with path.open('wb') as f:
  f.write(struct.pack('<I',len(items)))
  for words,_ in items:
   a=array.array('I',words)
   if sys.byteorder!='little':a.byteswap()
   f.write(a.tobytes())
def prepare(folder,name):
 target=folder/name;target.mkdir()
 with tarfile.open(fileobj=io.BytesIO(subprocess.check_output(['git','archive',SOURCE,'gpu'],cwd=R))) as a:a.extractall(target,filter='data')
 if name=='candidate':
  path=target/'gpu/enemy_target_runtime.slang';s=path.read_text()
  patches=[(
   'uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);\n        if(d.kind!=0 || d.stat!=S_taunt || s.alive[row]==0 || !f64Less(when,s.end[row])) continue;\n        if(d.enemyBuff!=0)',
   'uint row=s.orderedRows[pass],definition=s.carrierDefinition[row];\n        if(definition_kind(s.inputBase,definition)!=0 || definition_stat(s.inputBase,definition)!=S_taunt || s.alive[row]==0 || !f64Less(when,s.end[row])) continue;\n        if(definition_enemyBuff(s.inputBase,definition)!=0)'),
   ('if(member) mask|=1U<<d.owner;','if(member) mask|=1U<<definition_owner(s.inputBase,definition);'),
   ('uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);\n        if(d.kind==0 && d.stat==S_stealth && d.enemyBuff==0 && queryRecipient(s,row,who,when)) return true;',
    'uint row=s.orderedRows[pass],definition=s.carrierDefinition[row];\n        if(definition_kind(s.inputBase,definition)==0 && definition_stat(s.inputBase,definition)==S_stealth && definition_enemyBuff(s.inputBase,definition)==0 && queryRecipient(s,row,who,when)) return true;'),
   ('uint row=s.orderedRows[pass];Definition d=residentDefinition(s,row);\n        if(d.kind!=0 || s.alive[row]==0 || !f64Less(when,s.end[row]) || (s.activeRecipients[row]&(1U<<who))==0) continue;\n        if(d.stat!=S_atk_pct && d.stat!=S_atk_flat && d.stat!=S_atk_caster_based_pct) continue;',
    'uint row=s.orderedRows[pass],definition=s.carrierDefinition[row];\n        if(definition_kind(s.inputBase,definition)!=0 || s.alive[row]==0 || !f64Less(when,s.end[row]) || (s.activeRecipients[row]&(1U<<who))==0) continue;\n        uint stat=definition_stat(s.inputBase,definition);\n        if(stat!=S_atk_pct && stat!=S_atk_flat && stat!=S_atk_caster_based_pct) continue;'),
   ('if(d.stat==S_atk_pct) percent=f64Add(percent,value);\n        else if(d.stat==S_atk_flat) flat=f64Add(flat,value);\n        else flat=f64Add(flat,f64Mul(s.baseAttack[d.owner],f64Div(value,HUNDRED)));',
    'if(stat==S_atk_pct) percent=f64Add(percent,value);\n        else if(stat==S_atk_flat) flat=f64Add(flat,value);\n        else flat=f64Add(flat,f64Mul(s.baseAttack[definition_owner(s.inputBase,definition)],f64Div(value,HUNDRED)));'),
   ('Definition d=readDefinition(s.inputBase,row);\n        if(d.stat!=S_taunt && d.stat!=S_stealth) continue;',
    'uint stat=definition_stat(s.inputBase,row);\n        if(stat!=S_taunt && stat!=S_stealth) continue;\n        Definition d=readDefinition(s.inputBase,row);')]
  for before,after in patches:
   assert s.count(before)==1,before;s=s.replace(before,after)
  path.write_text(s)
 wrapper=target/(name+'_enemy_target_scalar_runtime.slang');wrapper.write_text('#include "gpu/event_runtime.slang"\n');return wrapper.relative_to(R).as_posix()
def main():
 assert ABI==0x50455673
 audit=load('portable-enemy-target-efficiency-plan');assert audit['candidate_source_audit_completed']
 for path,digest in audit['candidate_source_audit_sha256'].items():assert sha(R/path)==digest,path
 barrier=load('portable-enemy-target-timing-order');broad=load('portable-enemy-target-broad-validation');core=load('portable-combat-metal')
 assert barrier['passed'] and not barrier['verification_processes'] and barrier['windows_execution_and_transfer_terminal']
 assert broad['passed'] and broad['mac_gates']==52 and broad['source_commit']==SOURCE and core['passed']
 subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=R,check=True)
 folder=P/'portable-build'/('enemy-target-scalar-benchmark-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 paths={name:prepare(folder,name) for name in ('control','candidate')};one,many=rt.execute,rt.execute_batches
 changed=[p.relative_to(folder/'control').as_posix() for p in (folder/'control/gpu').rglob('*') if p.is_file() and p.read_bytes()!=(folder/'candidate'/p.relative_to(folder/'control')).read_bytes()];assert changed==['gpu/enemy_target_runtime.slang'],changed
 assert (folder/'control/gpu/event_runtime.slang').read_bytes()==(folder/'candidate/gpu/event_runtime.slang').read_bytes()
 (folder/'candidate-source-audit.json').write_text(json.dumps(dict(passed=True,changed_files=changed,runtime_layout_unchanged=True,input_words=L['INPUT_WORDS'],output_words=L['OUTPUT_WORDS'],candidate_module_sha256=sha(folder/'candidate/gpu/enemy_target_runtime.slang'),tool_sha256=sha(__file__)),indent=2)+'\n')
 def run(name,items,label):
  captured=folder/label;captured.mkdir();write_input(captured/'input.bin',items)
  def single(source,*a,**kw):assert source=='gpu/event_runtime.slang';return one(paths[name],*a,**kw)
  def multiple(source,*a,**kw):assert source=='gpu/event_runtime.slang';return many(paths[name],*a,**kw)
  rt.execute=single;rt.execute_batches=multiple
  try:raw,e=rt.dispatch_programs(items,backend='metal')
  finally:rt.execute=one;rt.execute_batches=many
  (captured/'readback.bin').write_bytes(raw);(captured/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
  e['captured']=str(captured);assert e['input_sha256']==sha(captured/'input.bin') and e['output_sha256']==sha(captured/'readback.bin')
  return raw,e
 parity={}
 suites=[('core',Path(core['enemy_target_existing_parity']['replay_source'])/'input.bin',core,4682)]
 for label,report,count in [('physical','portable-hp-attack-physical-metal',80),('health','portable-health-runtime-metal',20)]:
  proof=load(report);suites.append((label,Path(proof['captured'])/'input.bin',proof,count))
 for label,path,proof,count in suites:
  items=read_input(path);assert len(items)==count;parity[label]={}
  for name in paths:
   raw,e=run(name,items,'full-'+label+'-'+name);del raw
   assert e['input_sha256']==proof['input_sha256'] and e['output_sha256']==proof['output_sha256'],(label,name,e['captured'])
   parity[label][name]=e;print('full parity',label,name,count,flush=True)
  del items
 save('portable-enemy-target-scalar-parity',dict(passed=True,source_commit=SOURCE,parity=parity,production_adopted=False,captured=str(folder)))
 spec=importlib.util.spec_from_file_location('hp_benchmark_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 fixtures=v.fixtures();lookup={c['name']:c for c in fixtures}
 enemy=[c for c in fixtures if c.get('enemy_target_reference')]
 workloads={'ordinary':lookup['auto-magazine-reload'],'long-rng':lookup['enemy-long-rng-190'],'mode-enemy-domain':lookup['mode-enemy-domain-00']}
 for label,rule in [('random-dense','random:3'),('rank-dense','top_atk:3'),('slot-dense','slot:1,2,3'),('all-dense','all')]:
  pool=[c for c in enemy if any(a['target']==rule for a in c.get('enemy_targeting',{}).get('attacks',{}).values()) and any(cmd[1]==4 for cmd in c['script'])]
  chosen=copy.deepcopy(max(pool,key=lambda c:len(c['effects'])));chosen['name']='scalar-benchmark-'+label
  chosen.pop('expected_queries',None);chosen['expected_queries']=[]
  for index in range(64):
   chosen['effects'].append(dict(name='irrelevant crit '+str(index),source='스킬1',type='buff',stat='crit_dmg',target='self',fixed_value=0,duration=-1,max_stack=1,trigger=dict(timing=['battle_start'],condition=[])))
   chosen.setdefault('owners',[0]*(len(chosen['effects'])-1)).append(index%5)
  workloads[label]=chosen
 workload_items={k:v.compile_case(c) for k,c in workloads.items()}
 (folder/'workloads.json').write_text(json.dumps(workloads,ensure_ascii=False,indent=2)+'\n')
 rows={}
 for label,program in workload_items.items():
  items=[program]*1024;samples={n:[] for n in paths};baseline=None
  for sample in range(4):
   for name in (list(paths) if sample%2==0 else list(reversed(paths))):
    raw,e=run(name,items,label+'-'+str(sample)+'-'+name)
    if baseline is None:baseline=raw
    assert raw==baseline,('Workload difference retained; no retry',e['captured'])
    if sample==0:
     decoded_words=array.array('I');decoded_words.frombytes(raw[:L['OUTPUT_WORDS']*4])
     if sys.byteorder!='little':decoded_words.byteswap()
     decoded=rt.decode(decoded_words,program[1])
     if label.endswith('-dense'):
      from portable_enemy_target_oracle import compare
      compare(workloads[label],decoded,v.contains)
     elif label=='mode-enemy-domain':
      from portable_mode_enemy_name_oracle import compare
      compare(workloads[label],decoded,v.contains)
    samples[name].append(dict(warmup=sample==0,**e));print(label,sample,name,e['transport']['gpu_seconds'],flush=True)
  med={n:statistics.median(e['transport']['gpu_seconds'] for e in values[1:]) for n,values in samples.items()}
  ranges={n:[min(e['transport']['gpu_seconds'] for e in values[1:]),max(e['transport']['gpu_seconds'] for e in values[1:])] for n,values in samples.items()}
  ratio=med['candidate']/med['control'];rows[label]=dict(programs=1024,samples=samples,median_gpu_seconds=med,ranges=ranges,candidate_to_control_ratio=ratio,improves=ratio<=.98 and ranges['candidate'][1]<ranges['control'][0],regresses=ratio>=1.02 and ranges['candidate'][0]>ranges['control'][1])
  save('portable-enemy-target-scalar-benchmark-progress',dict(complete=False,source_commit=SOURCE,workloads=rows,captured=str(folder)))
 criteria=any(x['improves'] for k,x in rows.items() if k in ('random-dense','rank-dense','slot-dense')) and not any(x['regresses'] for x in rows.values())
 save('portable-enemy-target-scalar-benchmark',dict(passed=True,source_commit=SOURCE,criteria_met=criteria,production_adopted=False,workloads=rows,parity=parity,timing_order=barrier,captured=str(folder),tool_sha256=sha(__file__),scope='Apple M5 seven local workloads:ordinary,long RNG,mode/enemy alias,and four dense authored victim rules. Alternating order,warmup+3 samples. Full4682+80+20 parity before timing. No CUDA speed/full-roster speed/physical peak memory claim;production unchanged pending adoption verification.'))
 print('Efficiency criteria met:',criteria,'production unchanged',flush=True)
if __name__=='__main__':main()
