"""Bounded Metal measurement of physical-shot bullet carrier selection; not full battle performance."""
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
    fixture=ROOT/'tests/fixtures/portable-bullet-benchmark.json';case=json.loads(fixture.read_text());program,metadata=v.compile_case(case)
    count=8;packed=struct.pack('<'+'I'*(1+count*L['INPUT_WORDS']),count,*(program*count))
    source='gpu/benchmark_bullet_scan.slang' if args.label=='before' else 'gpu/event_runtime.slang';samples=[]
    for _ in range(3):
        raw,evidence=execute(source,'portableEvents',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend='metal')
        words=struct.unpack('<'+'I'*(count*L['OUTPUT_WORDS']),raw)
        for i in range(count):
            actual=decode(words[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],metadata)
            assert actual['status']==0 and actual['queries'][0]['damage']==[181800]*5, (actual['status'],actual['queries'][0]['damage'],actual['weapons'],actual['carriers'][-1])
            assert actual['bullet_lifetimes']['active_carriers']==1
            carrier=actual['carriers'][-1]
            assert carrier['active'] and carrier['recipient_bullets']==[2147483468]*5
        samples.append({k:evidence[k] for k in ('transport','input_sha256','output_sha256','source_sha256')})
    assert len({s['output_sha256'] for s in samples})==1
    report=dict(passed=True,gpu_execution_verified=True,backend='metal',strategy='scan_all_residents' if args.label=='before' else 'ordered_active_bullet_list',
                scope='8 programs, 256 carriers including one finite-bullet buff, 5 shooters/900 physical packets over 3 seconds each; not full battle or catalog',
                fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),samples=samples,
                median_gpu_seconds=statistics.median(s['transport']['gpu_seconds'] for s in samples))
    if args.label=='after':
        before=json.loads((ROOT/'research/portable-bullet-benchmark-before.json').read_text())
        for key in ('input_sha256','output_sha256'):assert before['samples'][0][key]==samples[0][key]
        assert before['fixture_sha256']==report['fixture_sha256']
        report['median_ratio_to_before']=report['median_gpu_seconds']/before['median_gpu_seconds']
    (ROOT/f'research/portable-bullet-benchmark-{args.label}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'}))


if __name__=='__main__':main()
