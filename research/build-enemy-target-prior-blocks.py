"""Build immutable per-block proof from the completed4070-input capture; no GPU."""
import hashlib,json,struct,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[1];PRIOR=subprocess.check_output(['git','rev-parse','89c19e3'],cwd=R,text=True).strip()
def main():
 report=json.loads(subprocess.check_output(['git','show',PRIOR+':research/portable-combat-metal.json'],cwd=R));folder=Path(report['mode_entry_existing_parity']['replay_source']);assert report['passed']
 names=[c['name'] for c in report['cases']]+[c['name'] for c in report['rejected_cases']];assert len(names)==4070
 blocks=[];ih=hashlib.sha256();oh=hashlib.sha256()
 with (folder/'input.bin').open('rb') as inputs,(folder/'readback.bin').open('rb') as outputs:
  header=inputs.read(4);assert struct.unpack('<I',header)[0]==4070;ih.update(header)
  for i,name in enumerate(names):
   source=inputs.read(86016*4);output=outputs.read(159744*4);assert len(source)==86016*4 and len(output)==159744*4;ih.update(source);oh.update(output)
   blocks.append(dict(index=i,name=name,input_abi=struct.unpack_from('<I',source)[0],sha256=hashlib.sha256(output).hexdigest()))
  assert not inputs.read(1) and not outputs.read(1)
 assert ih.hexdigest()==report['input_sha256'] and oh.hexdigest()==report['output_sha256']
 result=dict(passed=True,prior_proof_commit=PRIOR,input_sha256=ih.hexdigest(),output_sha256=oh.hexdigest(),blocks=blocks)
 (R/'research/portable-enemy-target-prior-blocks.json').write_text(json.dumps(result,indent=2)+'\n');print('4070 prior blocks,input ABI headers and SHA verified')
if __name__=='__main__':main()
