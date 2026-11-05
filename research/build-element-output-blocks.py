"""Persist per-program byte hashes from the CUDA-matching captured baseline."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'research';m=json.loads((P/'portable-combat-metal.json').read_text());w=json.loads((P/'windows-portable-element-v65.json').read_text());assert m['passed'] and w['passed'] and m['output_sha256']==w['output_sha256']
labels=[dict(name=c['name'],kind='positive') for c in m['cases']]+[dict(name=c['name'],kind='rejection') for c in m['rejected_cases']];assert len(labels)==2182
stride=159744*4;h=hashlib.sha256();blocks=[]
with (P/'portable-build/element-reproduction/run-0.bin').open('rb') as f:
 for i,label in enumerate(labels):
  b=f.read(stride);assert len(b)==stride;h.update(b);blocks.append(dict(index=i,**label,expected_status=m['expected_statuses'][i],sha256=hashlib.sha256(b).hexdigest()))
 assert not f.read(1)
assert h.hexdigest()==m['output_sha256']
r=dict(passed=True,source_commit='14c8e2e61fd6eeb9950a13c76f217ae62ca82fd9',programs=2182,input_words=86016,output_words=159744,input_sha256=m['input_sha256'],output_sha256=h.hexdigest(),blocks=blocks,source_sha256=m['source_sha256'],validation_sha256=m['validation_sha256'],baseline_cuda_report='windows-portable-element-v65.json',initial_metal_finding_open=True,scope='Successful recorded baseline matches full CUDA readback;does not reconstruct the unretained initial failing readback')
(P/'portable-element-baseline-output-blocks.json').write_text(json.dumps(r,indent=2)+'\n');print('2182 CUDA-matching output block hashes preserved')
