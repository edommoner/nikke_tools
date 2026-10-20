"""Canonical authored policy into isolated full executor; native closures after readback."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts'),str(R/'research')]
import portable_runtime as runtime,portable_enemy_specs as enemy_specs
from portable_specs import LIMITS as L
from portable_enemy_target_specs import ABI,pack,META_BASE,RNG_BASE,QUERY_BASE
from enemy_target_native import observe

def core_module():
 s=importlib.util.spec_from_file_location('enemy_target_common',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v

def compile_case(c,v):
 # Temporary host admission only; the final wire contains rules,never selected masks.
 temporary=copy.deepcopy(c);temporary.pop('enemy_targeting',None)
 for cmd in temporary['script']:
  if cmd[1]==32:cmd[1]=31;cmd[4]=31
 buffs,enemies=runtime.BUFFS,enemy_specs.ENEMY_BUFF_STATS
 try:
  runtime.BUFFS=buffs|{'taunt','stealth'};enemy_specs.ENEMY_BUFF_STATS=enemies|{'taunt'}
  words,metadata=v.compile_case(temporary)
 finally:runtime.BUFFS=buffs;enemy_specs.ENEMY_BUFF_STATS=enemies
 words[0]=ABI
 for step,cmd in enumerate(c['script']):
  if cmd[1]==32:
   assert cmd[3]==0 and cmd[4]==0 and cmd[5]==-1
   at=L['COMMAND_BASE']+step*8;words[at]=32;words[at+4]=0;words[at+5]=0
 metadata['enemy_targeting']=pack(words,c.get('enemy_targeting'),c['script'],list(zip(c['effects'],c.get('owners',[0]*len(c['effects'])))))
 return words,metadata

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['metal','cuda'],default='metal');p.add_argument('--native-only',action='store_true');p.add_argument('--limit',type=int);a=p.parse_args();v=core_module()
 prep=json.loads((R/'research/portable-enemy-target-candidate-preparation.json').read_text())
 for path,digest in prep['source_sha256'].items():assert hashlib.sha256((R/path).read_bytes()).hexdigest()==digest,path
 cases=json.loads((R/'research/portable-enemy-target-inputs.json').read_text())['cases'];cases=cases[:a.limit] if a.limit is not None else cases
 validation=['app/portable_enemy_target_specs.py','research/enemy_target_native.py','research/verify-target-rng.py','research/verify-enemy-target-candidate.py','research/build-enemy-target-cases.py','research/portable-enemy-target-inputs.json']
 hashes={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in validation}
 programs=[compile_case(c,v) for c in cases];gpu=None;evidence={};folder=None
 if not a.native_only:
  folder=R/'research/portable-build'/('enemy-target-component-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
  (folder/'input.bin').write_bytes(runtime.pack_programs(programs));one,many=runtime.execute,runtime.execute_batches
  def single(source,*a,**kw):assert source=='gpu/event_runtime.slang';return one(prep['shader'],*a,**kw)
  def multiple(source,*a,**kw):assert source=='gpu/event_runtime.slang';return many(prep['shader'],*a,**kw)
  runtime.execute=single;runtime.execute_batches=multiple
  try:raw,evidence=runtime.dispatch_programs(programs,backend=a.backend)
  finally:runtime.execute=one;runtime.execute_batches=many
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
  gpu=array.array('I');gpu.frombytes(raw)
  if sys.byteorder!='little':gpu.byteswap()
 rows=[]
 for i,c in enumerate(cases):
  native=actual=None
  try:
   native=observe(c)
   if gpu is not None:
    block=gpu[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']];actual=runtime.decode(block,programs[i][1]);assert actual['status']==0,actual['status']
    for q,n in zip(actual['queries'],native['queries']):
     # Conditional fields follow the existing decoder's feature gates.
     expected={k:value for k,value in n.items() if k!='protection' or 'protection' in q};v.contains(q,expected,c['name']+'.native-query')
    assert len(actual['queries'])==len(native['queries'])
    selection=[]
    for step in programs[i][1]['enemy_targeting']['steps']:
     b=QUERY_BASE+step*8;selection.append(dict(step=step,mask=block[b],order=block[b+1],targets=[((block[b+1]>>(3*j))&7)-1 for j in range(5) if ((block[b+1]>>(3*j))&7)!=0],taunt_mask=block[b+2],pool_mask=block[b+3],draws_before=block[b+4],draws_after=block[b+5],rejects_after=block[b+6],valid=block[b+7]))
    actual['enemy_selection']=selection;assert selection==native['selection'],('Enemy selection/RNG consumption',selection,native['selection'])
    def number(at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    hits=[]
    for selected in selection:
     for who in selected['targets']:
      assert 0<=who<5
      index=selected['step']*5+who
      records=[(L['PROTECTION_HIT_BASE']+index*16,who)]+[(L['SPLIT_HIT_BASE']+(index*4+k)*16,None) for k in range(4)]
      for at,owner in records:
       if block[at+2]:hits.append(dict(time=number(at),owner=(block[at+3]>>3)&7 if owner is None else owner,pierce=bool(block[at+3]&1),down=bool(block[at+3]&4),damage=number(at+4),shield=number(at+6),cover=number(at+8),decoy=number(at+10),hp=number(at+12),hp_after=number(at+14)))
    actual['enemy_hits']=hits;v.contains(hits,native['hits'],c['name']+'.native-ordered-hits')
    b=RNG_BASE;actual['enemy_rng']=dict(index=block[b],draws=block[b+1],samples=block[b+2],rejects=block[b+3],state=list(block[b+8:b+632]));assert actual['enemy_rng']==native['rng'],'RNG full state'
  except Exception as e:rows.append(dict(name=c['name'],passed=False,error=repr(e),native=native,actual=actual))
  else:rows.append(dict(name=c['name'],passed=True,native=native,actual=actual))
 assert hashes=={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in validation}
 suffix='native' if a.native_only else a.backend
 report=dict(passed=all(r['passed'] for r in rows),cases=rows,preparation=prep,captured=str(folder) if folder else None,production_adopted=False,cpu_selected_targets_used_as_gpu_input=False,cpu_rng_state_used_as_gpu_input=False,validation_sha256=hashes,**evidence)
 (R/f'research/portable-enemy-target-candidate-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert report['passed'],[(r['name'],r.get('error')) for r in rows if not r['passed']]
 print(len(rows),'native target/ordered landing/RNG cases match',suffix)
if __name__=='__main__':main()
