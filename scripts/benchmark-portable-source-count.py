"""Bounded Metal measurement of shared owned-source population counts; not full battle performance."""
import argparse,hashlib,json,statistics,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import decode
from portable_backend import execute
from portable_specs import LIMITS as L
import importlib.util
spec=importlib.util.spec_from_file_location('combat_verifier',ROOT/'scripts/verify-portable-combat.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--label',choices=('before','after'),required=True);args=parser.parse_args()
    fixture=ROOT/'tests/fixtures/portable-source-count-benchmark.json';case=json.loads(fixture.read_text());program,metadata=v.compile_case(case)
    count=64;packed=struct.pack('<'+'I'*(1+count*L['INPUT_WORDS']),count,*(program*count))
    source='gpu/benchmark_source_count_scan.slang' if args.label=='before' else 'gpu/event_runtime.slang';samples=[]
    for _ in range(3):
        raw,evidence=execute(source,'portableEvents',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend='metal')
        words=struct.unpack('<'+'I'*(count*L['OUTPUT_WORDS']),raw)
        for i in range(count):
            actual=decode(words[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],metadata)
            assert actual['status']==0
            assert actual['frames']==181 and actual['trace_total']==1920
            assert actual['source_queries'][0]['count']==32 and actual['source_queries'][0]['next_at']==3600
            assert actual['resource_trace_total']==0 and actual['resource_trace']==[]
            assert len(actual['queries'])==1 and actual['queries'][0]['damage']==[1920,0,0,0,0] and actual['queries'][0]['attack_buffs']==[32,0,0,0,0]
        samples.append({k:evidence[k] for k in ('transport','input_sha256','output_sha256','source_sha256')})
    assert len({s['output_sha256'] for s in samples})==1
    report=dict(passed=True,gpu_execution_verified=True,backend='metal',strategy='recompute_slot_expiries_for_every_reference' if args.label=='before' else 'memoize_population_by_time_and_refresh_epoch',
                scope='64 programs, 33 definitions, one 32-slot source, 32-hit referenced activation every 0.05 seconds for 3 seconds, 1920 one-damage packets each; desktop GPU contention not excluded; not full battle or catalog',
                fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),samples=samples,
                median_gpu_seconds=statistics.median(s['transport']['gpu_seconds'] for s in samples))
    if args.label=='after':
        before=json.loads((ROOT/'research/portable-source-count-benchmark-before.json').read_text())
        for key in ('input_sha256','output_sha256'):assert before['samples'][0][key]==samples[0][key]
        assert before['fixture_sha256']==report['fixture_sha256']
        report['median_ratio_to_before']=report['median_gpu_seconds']/before['median_gpu_seconds']
    (ROOT/f'research/portable-source-count-benchmark-{args.label}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'}))


if __name__=='__main__':main()
