"""Exact old4070 readback preservation with valid ABI72 ->73 only; no decode normalization."""
import array,datetime,hashlib,json,struct,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'app'))
import portable_runtime as runtime
from portable_specs import LIMITS as L
from portable_enemy_target_specs import ABI

def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
def main():
 prior=json.loads((R/'research/portable-combat-metal.json').read_text());assert prior['passed'] and len(prior['cases'])+len(prior['rejected_cases'])==4070
 preparation=json.loads((R/'research/portable-enemy-target-candidate-preparation.json').read_text())
 old=Path(prior['mode_entry_existing_parity']['replay_source']);assert sha(old/'input.bin')==prior['input_sha256'] and sha(old/'readback.bin')==prior['output_sha256']
 words=array.array('I');words.frombytes((old/'input.bin').read_bytes())
 if sys.byteorder!='little':words.byteswap()
 assert words[0]==4070 and len(words)==1+4070*L['INPUT_WORDS']
 programs=[];unchanged_headers=[]
 for i in range(4070):
  block=list(words[1+i*L['INPUT_WORDS']:1+(i+1)*L['INPUT_WORDS']])
  if block[0]==0x50455672:block[0]=ABI
  else:unchanged_headers.append(dict(index=i,abi=hex(block[0])))
  programs.append((block,{}))
 del words
 folder=R/'research/portable-build'/('enemy-target-prior-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 # Stream full logical input;dispatch groups remain bounded by the common runner.
 with (folder/'input.bin').open('wb') as f:
  f.write(struct.pack('<I',len(programs)))
  for block,_ in programs:
   a=array.array('I',block)
   if sys.byteorder!='little':a.byteswap()
   f.write(a.tobytes())
 one,many=runtime.execute,runtime.execute_batches
 def single(source,*a,**kw):assert source=='gpu/event_runtime.slang';return one(preparation['shader'],*a,**kw)
 def multiple(source,*a,**kw):assert source=='gpu/event_runtime.slang';return many(preparation['shader'],*a,**kw)
 runtime.execute=single;runtime.execute_batches=multiple
 try:raw,evidence=runtime.dispatch_programs(programs,backend='metal')
 finally:runtime.execute=one;runtime.execute_batches=many
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 passed=sha(folder/'readback.bin')==prior['output_sha256']
 report=dict(passed=passed,prior_proof_commit='89c19e3',prior_source_commit='39bce8aa5c9c5f29f0653e80fc69855f19ad5ad6',programs=4070,valid_abi_projection='72->73',intentional_invalid_headers_preserved=unchanged_headers,every_other_input_word_preserved=True,all_output_words_equal=passed,old_input_sha256=prior['input_sha256'],old_output_sha256=prior['output_sha256'],captured=str(folder),preparation=preparation,production_adopted=False,no_gpu_retry=True,**evidence)
 (R/'research/portable-enemy-target-prior-metal-parity.json').write_text(json.dumps(report,indent=2)+'\n')
 assert passed,'Old output difference captured; no unchanged GPU retry'
 print('All4070 old input blocks preserved except valid ABI;every output word exact. Invalid headers:',unchanged_headers)
if __name__=='__main__':main()
