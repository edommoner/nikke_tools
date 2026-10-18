"""Bounded Metal memo lookup/query-interest measurement; no whole-battle claim."""
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
    fixture=ROOT/'tests/fixtures/portable-lazy.json';case=next(c for c in json.loads(fixture.read_text())['cases'] if c['name']=='old-pending-sibling-protects-cache-during-long-recycling')
    program,metadata=v.compile_case(case);count=8
    packed=struct.pack('<'+'I'*(1+count*L['INPUT_WORDS']),count,*(program*count))
    source='gpu/benchmark_lazy_scan.slang' if args.label=='before' else 'gpu/event_runtime.slang';samples=[]
    for _ in range(3):
        raw,evidence=execute(source,'portableEvents',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend='metal')
        words=struct.unpack('<'+'I'*(count*L['OUTPUT_WORDS']),raw)
        for i in range(count):
            r=decode(words[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],metadata)
            assert r['status']==0;v.contains(r['queries'],case['expected_queries']);v.contains(r['lazy_cache'],case['expected_lazy_cache'])
            assert r['lazy_cache']['reuses']>=case['minimum_cache_reuses']
        samples.append({k:evidence[k] for k in ('transport','input_sha256','output_sha256','source_sha256')})
    assert len({s['output_sha256'] for s in samples})==1
    report=dict(passed=True,gpu_execution_verified=True,backend='metal',strategy='scan_memo_and_all_pending_query_interest' if args.label=='before' else 'memo_group_latest_hint_and_mapped_pending_interest',
                scope='8 programs, 20 GPU-generated seconds/1201 shots, pending healing snapshot protected while memo recycles; not full battle or catalog',
                fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),samples=samples,median_gpu_seconds=statistics.median(s['transport']['gpu_seconds'] for s in samples))
    if args.label=='after':
        before=json.loads((ROOT/'research/portable-lazy-benchmark-before.json').read_text())
        assert before['fixture_sha256']==report['fixture_sha256']
        for key in ('input_sha256','output_sha256'):assert before['samples'][0][key]==samples[0][key]
        report['median_ratio_to_before']=report['median_gpu_seconds']/before['median_gpu_seconds']
    (ROOT/f'research/portable-lazy-benchmark-{args.label}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'}))


if __name__=='__main__':main()
