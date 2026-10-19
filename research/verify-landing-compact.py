"""Shared codec boundaries and full wide/compact representation equivalence.
No timing claim; the wide control uses identical physics and current ABI.
"""
import array,copy,hashlib,importlib.util,json,random,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_runtime as runtime
from portable_backend import execute
from portable_specs import LIMITS as L

def codec_boundaries(backend):
 rng=random.Random(941)
 rows=[[0,0,0,0,0,0,0,0,1,1,1,0],[255,7,255,0x87654321,0xffffffff,0x7fefffff,1,0x80000000,256,256,32,0x7fffffff],[255,7,0xffffffff,0x12345678,1,0,0,0x3ff00000,1,256,32,0x7fffffff]]
 for _ in range(256):
  hits=rng.randint(1,256)
  rows.append([rng.randrange(256),rng.randrange(8),rng.choice([0xffffffff,rng.randrange(256)]),rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32),rng.getrandbits(32),rng.randint(1,hits),hits,rng.randint(1,32),rng.randrange(0x80000000)])
 good=len(rows)
 for offset,value in ((0,256),(1,8),(2,256),(2,0xfffffffe),(8,0),(8,257),(9,0),(9,257),(10,0),(10,33),(11,0x80000000)):
  row=rows[0].copy();row[offset]=value;rows.append(row)
 words=[len(rows)]+sum(rows,[]);packed=struct.pack('<'+'I'*len(words),*words)
 raw,evidence=execute('gpu/landing_codec_probe.slang','landingCodecProbe',packed,12,21,backend)
 out=struct.unpack('<'+'I'*(len(raw)//4),raw)
 for i,row in enumerate(rows):
  actual=out[i*21:(i+1)*21];assert actual[20]==int(i<good),(i,actual)
  if i<good:
   assert list(actual[8:20])==row,(i,row,actual)
   mask=256 if row[2]==0xffffffff else row[2]
   assert list(actual[:8])==[row[0]|row[1]<<8|mask<<11,row[3],*row[4:8],row[8]|row[9]<<9|row[10]<<18,row[11]]
 return dict(passed=True,valid_vectors=good,invalid_vectors=len(rows)-good,arbitrary_binary64_bits_preserved=True,**evidence)

def canonicalize(raw,count):
 wide=array.array('I');wide.frombytes(raw)
 if sys.byteorder!='little':wide.byteswap()
 compact=array.array('I',[0])*(count*L['OUTPUT_WORDS']);start=L['LANDING_STATE_BASE']
 for i in range(count):
  a=i*98304;b=i*L['OUTPUT_WORDS'];compact[b:b+start]=wide[a:a+start]
  for j in range(L['LANDINGS']):
   at=a+start+j*12;dst=b+start+j*8;r=wide[at:at+12];mask=256 if r[2]==0xffffffff else r[2]
   compact[dst:dst+8]=array.array('I',[r[0]|r[1]<<8|mask<<11,r[3],*r[4:8],r[8]|r[9]<<9|r[10]<<18,r[11]])
  assert not any(wide[a+start+L['LANDINGS']*12:a+98304])
 if sys.byteorder!='little':compact.byteswap()
 return compact.tobytes()

def main():
 backend='cuda' if '--backend' in sys.argv and sys.argv[sys.argv.index('--backend')+1]=='cuda' else 'metal'
 production_only='--production-only' in sys.argv
 if production_only:sys.argv.remove('--production-only')
 report=dict(passed=False,codec=codec_boundaries(backend));path=ROOT/f'research/portable-landing-compact-{backend}.json';path.write_text(json.dumps(report,indent=2)+'\n')
 sp=importlib.util.spec_from_file_location('vcompact',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
 def compare(source,entry,packed,input_words,output_words,backend):
  compact,evidence=execute(source,entry,packed,input_words,output_words,backend)
  wide,control=execute('gpu/benchmark_landing_wide.slang',entry,packed,input_words,98304,backend)
  count=struct.unpack_from('<I',packed)[0];normalized=canonicalize(wide,count)
  assert compact==normalized,'Wide and compact physics or scratch records differ'
  report.update(passed=True,batched_inputs=count,canonical_output_sha256=hashlib.sha256(normalized).hexdigest(),compact=evidence,wide=control,comparison='Every output word, including all 2048 historical receipt slots; only lossless record representation and zero alignment padding normalized',input_words=input_words,output_words=output_words,wide_output_words=98304,bytes_saved_per_program=(98304-output_words)*4,timing_measured=False)
  path.write_text(json.dumps(report,indent=2)+'\n')
  return compact,evidence
 if production_only:
  v.main();report.update(passed=True,production_only=True,production_report=f'portable-combat-{backend}.json',wide_control_run=False,timing_measured=False);path.write_text(json.dumps(report,indent=2)+'\n');return
 runtime.execute=compare
 v.main()
 batch=dict(report);(ROOT/f'research/portable-landing-compact-batch-{backend}.json').write_text(json.dumps(batch,indent=2)+'\n')
 # Probe the live queue decoder, which whole-timeline fixtures flush at the end.
 case=copy.deepcopy(v.fixtures()[-20]);case['script']=[[0,24,0,0,0,-1,0,0],[0,2,0,0,-1,0,0,0]]
 result=runtime.run_programs([v.compile_case(case)],backend=backend)['results'][0]
 queue=result['landing_queue'];assert len(queue['entries'])==2 and queue['enqueued']==2 and queue['landed']==0
 assert result['queries'][0]['damage'][0]==1000 and result['queries'][0]['allies'][0]['hp']==150
 for i,r in enumerate(queue['entries']):assert r['hit']==i+1 and r['hits']==2 and r['amount']==1000 and r['time']==0
 report.update(passed=True,live_queue_decoder_verified=True,live_queue=queue,batch_comparison_report=f'portable-landing-compact-batch-{backend}.json',total_comparison_inputs=batch['batched_inputs']+1)
 path.write_text(json.dumps(report,indent=2)+'\n');print('Compact receipt boundaries and all-word equivalence passed',flush=True)
if __name__=='__main__':main()
