"""Isolated candidate retains every byte of the previous3539 outputs."""
import datetime,hashlib,json,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_backend import execute_batches
from portable_specs import LIMITS as L

def file_sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  while b:=f.read(8*1024*1024):h.update(b)
 return h.hexdigest()
def main():
 prior_commit=subprocess.check_output(['git','rev-parse','d181fcd'],cwd=ROOT,text=True).strip();prior=json.loads(subprocess.check_output(['git','show',prior_commit+':research/portable-combat-metal.json'],cwd=ROOT));p=prior['hp_attack_existing_parity']
 assert prior['passed'] and file_sha(p['input_path'])==prior['input_sha256'] and file_sha(p['raw_path'])==prior['output_sha256']
 prep=json.loads((ROOT/'research/portable-mode-entry-candidate-preparation.json').read_text());folder=ROOT/'research/portable-build'/('mode-entry-prior-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir()
 batches=[];exceptions=[];stride=L['INPUT_WORDS']*4
 with Path(p['input_path']).open('rb') as stream,(folder/'input.bin').open('wb') as saved:
  count=struct.unpack('<I',stream.read(4))[0];assert count==3539;saved.write(struct.pack('<I',count))
  for start in range(0,count,2048):
   n=min(2048,count-start);data=bytearray(stream.read(n*stride));assert len(data)==n*stride
   for j in range(n):
    header=struct.unpack_from('<I',data,j*stride)[0]
    if header==0x50455671:struct.pack_into('<I',data,j*stride,0x50455672)
    else:
     assert header==0x50455670 and start+j==3525,(start+j,hex(header));exceptions.append(dict(index=start+j,header=hex(header)))
   saved.write(data);batches.append(struct.pack('<I',n)+data)
  assert not stream.read(1)
 results=execute_batches(prep['shader'],'portableEvents',batches,L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend='metal')
 with (folder/'readback.bin').open('wb') as f:
  for raw,e in results:f.write(raw)
 evidence=[e for raw,e in results];(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 actual=file_sha(folder/'readback.bin');changed=[]
 with Path(p['raw_path']).open('rb') as a,(folder/'readback.bin').open('rb') as b:
  for i in range(count):
   old=a.read(L['OUTPUT_WORDS']*4);new=b.read(L['OUTPUT_WORDS']*4)
   if old!=new:changed.append(dict(index=i,prior_sha256=hashlib.sha256(old).hexdigest(),candidate_sha256=hashlib.sha256(new).hexdigest()))
 result=dict(passed=not changed and actual==prior['output_sha256'],prior_proof_commit=prior_commit,prior_inputs=3539,captured=str(folder),input_sha256=file_sha(folder/'input.bin'),output_sha256=actual,prior_input_sha256=prior['input_sha256'],prior_output_sha256=prior['output_sha256'],changed=changed,input_projection='Only valid ABI71 headers become72;the intentional invalid70 header at3525 is preserved. Every other input byte unchanged.',invalid_headers_preserved=exceptions,all_prior_output_words_equal=not changed,no_output_normalization=True,no_unchanged_gpu_retry=True,preparation=prep,evidence=evidence,production_adopted=False)
 (ROOT/'research/portable-mode-entry-candidate-prior-parity.json').write_text(json.dumps(result,indent=2)+'\n');assert result['passed'],changed;print('All3539 prior output words preserved by isolated entry-delay candidate')
if __name__=='__main__':main()
