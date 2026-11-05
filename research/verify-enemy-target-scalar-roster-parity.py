"""Compare retained full input/readback blocks across host/CPU fixes,no GPU run."""
import hashlib,json,struct,subprocess
from pathlib import Path
R=Path('/Users/edo/Documents/ChatGPT/nikke_tools');P=R/'research';IN=86016*4;OUT=159744*4

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def blocks(report):
 result={}
 for batch in report['gpu_batches']:
  inp=Path(batch['captured']['input_path']);out=Path(batch['captured']['readback_path']);assert sha(inp)==batch['input_sha256'] and sha(out)==batch['output_sha256']
  with inp.open('rb') as fi,out.open('rb') as fo:
   assert struct.unpack('<I',fi.read(4))[0]==len(batch['case_indices'])
   for index in batch['case_indices']:
    c=report['cases'][index];a=fi.read(IN);b=fo.read(OUT);assert len(a)==IN and len(b)==OUT
    key=(c['character'],c['grown']);assert key not in result;result[key]=dict(input_sha256=hashlib.sha256(a).hexdigest(),output_sha256=hashlib.sha256(b).hexdigest(),source_sha256=batch['source_sha256'])
 return result
old=load(P/'portable-build/enemy-target-1db1a3f-initial/portable-roster-battles-metal.json');expected=blocks(old);assert len(expected)==156
candidate=load(P/'portable-mode-enemy-name-candidate-metal.json');assert candidate['passed'] and len(candidate['cases'])==2
folder=Path(candidate['captured']);assert sha(folder/'input.bin')==candidate['evidence']['input_sha256'] and sha(folder/'readback.bin')==candidate['evidence']['output_sha256']
with (folder/'input.bin').open('rb') as fi,(folder/'readback.bin').open('rb') as fo:
 assert struct.unpack('<I',fi.read(4))[0]==2
 for c in candidate['cases']:
  key=(c['character'],c['grown']);assert key not in expected;expected[key]=dict(input_sha256=hashlib.sha256(fi.read(IN)).hexdigest(),output_sha256=hashlib.sha256(fo.read(OUT)).hexdigest(),source_sha256=candidate['evidence']['source_sha256'])
current=load(P/'portable-roster-battles-metal.json');assert current['passed'] and len(current['cases'])==158;actual=blocks(current);assert actual.keys()==expected.keys()
changed=set()
for key,data in actual.items():
 assert data['input_sha256']==expected[key]['input_sha256'] and data['output_sha256']==expected[key]['output_sha256'],key
 assert data['source_sha256'].keys()==expected[key]['source_sha256'].keys()
 changed.update(p for p,h in data['source_sha256'].items() if h!=expected[key]['source_sha256'][p])
assert changed=={'gpu/enemy_target_runtime.slang'},changed
for data in actual.values():
 for path,digest in data['source_sha256'].items():assert sha(R/path)==digest
report=dict(passed=True,source_commit='73570451569dce424667e37f4729e475ea6b0a86',audit_checkout_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),audit_tool_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),original156_readback_blocks_preserved=True,isolated2_weapon_enemy_name_blocks_preserved=True,profiles=158,all158_input_words_equal=True,all158_output_words_equal=True,gpu_source_identical=False,changed_gpu_source_paths=sorted(changed),normalization=False,gpu_executions=0,scope='One GPU source module changed for scalar filtering. Full block equality against initial156 Metal profiles plus isolated2 Metal profiles across host admission and CPU synchronization fixes. Initial six failures remain archived;this proof does not reclassify their earlier CPU checks as passed.')
(P/'portable-enemy-target-scalar-roster-parity.json').write_text(json.dumps(report,indent=2)+'\n');print('All158 original input/readback blocks preserved exactly after host and CPU fixes')
