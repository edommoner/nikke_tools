"""Sequential bounded Metal codec timing, only after all verification ends."""
import argparse,copy,hashlib,importlib.util,json,statistics,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_backend import execute
from portable_runtime import decode
from portable_specs import LIMITS as L
sp=importlib.util.spec_from_file_location('receipt_comparison',ROOT/'research/verify-landing-compact.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
sp=importlib.util.spec_from_file_location('receipt_cases',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(sp);sp.loader.exec_module(v)
def main():
 p=argparse.ArgumentParser();p.add_argument('--label',choices=('wide','compact'),required=True);p.add_argument('--workload',choices=('two-receipts','full-2048'),required=True);a=p.parse_args()
 cases=json.loads((ROOT/'tests/fixtures/portable-landings.json').read_text())['cases'];case=cases[0] if a.workload=='two-receipts' else cases[-1];count=64 if a.workload=='two-receipts' else 16
 program,meta=v.compile_case(case);words=[count]+program*count;packed=struct.pack('<'+'I'*len(words),*words)
 source='gpu/benchmark_landing_wide.slang' if a.label=='wide' else 'gpu/event_runtime.slang';stride=98304 if a.label=='wide' else L['OUTPUT_WORDS'];samples=[]
 for iteration in range(4):
  raw,evidence=execute(source,'portableEvents',packed,L['INPUT_WORDS'],stride,backend='metal')
  normalized=m.canonicalize(raw,count) if a.label=='wide' else raw;h=hashlib.sha256(normalized).hexdigest()
  output=struct.unpack('<'+'I'*(len(normalized)//4),normalized)
  for i in range(count):
   actual=decode(output[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],meta);assert actual['status']==0;v.contains(actual['queries'],case['expected_queries']);assert actual['landing_queue']['peak']==(2 if a.workload=='two-receipts' else 2048)
  if iteration:samples.append(dict(**evidence,canonical_output_sha256=h))
 assert len({r['canonical_output_sha256'] for r in samples})==1
 report=dict(passed=True,backend='metal',label=a.label,workload=a.workload,programs=count,output_words=stride,bytes_per_program=stride*4,median_gpu_seconds=statistics.median(r['transport']['gpu_seconds'] for r in samples),samples=samples,warmup_dispatches=1,measured_dispatches=3,scope='Bounded authored inputs, unchanged physics; desktop GPU contention not excluded, no full battle or roster performance claim',fixture_sha256=hashlib.sha256((ROOT/'tests/fixtures/portable-landings.json').read_bytes()).hexdigest(),validation_sha256={str(Path(__file__).relative_to(ROOT)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},comparison_helper_sha256=hashlib.sha256((ROOT/'research/verify-landing-compact.py').read_bytes()).hexdigest())
 if a.label=='compact':
  old=json.loads((ROOT/f'research/portable-landing-{a.workload}-wide-benchmark.json').read_text())
  for key in ('input_sha256','canonical_output_sha256'):assert old['samples'][0][key]==samples[0][key]
  report.update(median_ratio_to_wide=report['median_gpu_seconds']/old['median_gpu_seconds'],bytes_saved_per_program=old['bytes_per_program']-report['bytes_per_program'])
 (ROOT/f'research/portable-landing-{a.workload}-{a.label}-benchmark.json').write_text(json.dumps(report,indent=2)+'\n');print(a.workload,a.label,report['median_gpu_seconds'],flush=True)
if __name__=='__main__':main()
