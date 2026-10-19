"""Bounded sequential Metal timing; functional gates must finish first."""
import argparse,hashlib,importlib.util,json,statistics,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_backend import execute
from portable_runtime import decode
from portable_specs import LIMITS as L
spec=importlib.util.spec_from_file_location('staged_benchmark_cases',ROOT/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
def main():
 p=argparse.ArgumentParser();p.add_argument('--label',choices=('before','after'),required=True);p.add_argument('--definitions',type=int,choices=(33,256),required=True);args=p.parse_args()
 fixture=ROOT/'tests/fixtures/portable-staged-index-benchmark.json';case=next(c for c in json.loads(fixture.read_text())['cases'] if len(c['effects'])==args.definitions)
 program,metadata=v.compile_case(case);count=64;packed=struct.pack('<'+'I'*(1+count*L['INPUT_WORDS']),count,*(program*count));source='gpu/benchmark_staged_full_scan.slang' if args.label=='before' else 'gpu/event_runtime.slang';samples=[]
 for _ in range(3):
  raw,evidence=execute(source,'portableEvents',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend='metal');words=struct.unpack('<'+'I'*(count*L['OUTPUT_WORDS']),raw)
  for i in range(count):
   actual=decode(words[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],metadata);assert actual['status']==0;v.contains(actual['queries'],case['expected_queries']);assert actual['trace_total']==650;assert len(actual['staged_applications'])==1 and actual['staged_applications'][0]['index']==64
  samples.append({k:evidence[k] for k in ('transport','input_sha256','output_sha256','source_sha256')})
 assert len({s['output_sha256'] for s in samples})==1
 report=dict(passed=True,backend='metal',gpu_execution_verified=True,definitions=args.definitions,programs=count,samples=samples,fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),validation_sha256={str(Path(__file__).relative_to(ROOT)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},median_gpu_seconds=statistics.median(s['transport']['gpu_seconds'] for s in samples),scope='64 programs, one staged definition, ten 64-step registrations, 650 damage packets per program; no desktop GPU exclusion or full-battle performance claim')
 if args.label=='after':
  before=json.loads((ROOT/f'research/portable-staged-index-{args.definitions}-before.json').read_text())
  for key in ('input_sha256','output_sha256'):assert before['samples'][0][key]==samples[0][key]
  assert before['fixture_sha256']==report['fixture_sha256'];report['median_ratio_to_before']=report['median_gpu_seconds']/before['median_gpu_seconds']
 (ROOT/f'research/portable-staged-index-{args.definitions}-{args.label}.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='samples'}))
if __name__=='__main__':main()
