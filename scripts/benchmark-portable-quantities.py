"""Metal-only measurement of the shared source-group quantity collector.
A bounded authored workload, not full-roster battle performance.
"""
import argparse,hashlib,json,statistics,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker
from portable_runtime import compile_program,decode
from portable_backend import execute
from portable_specs import LIMITS as L
from timer_registry_cases import NAMES


def main():
    p=argparse.ArgumentParser();p.add_argument('--label',choices=['before','after'],required=True);args=p.parse_args()
    fixture=ROOT/'tests/fixtures/portable-quantity-benchmark.json';case=json.loads(fixture.read_text())
    chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES]
    program=compile_program(chars,[(e,NAMES[0]) for e in case['effects']],case['script'],[1000]*5,combat=case['combat'])
    source='gpu/benchmark_quantity_scan.slang' if args.label=='before' else 'gpu/event_runtime.slang'
    packed=struct.pack('<'+'I'*(1+64*L['INPUT_WORDS']),64,*(program[0]*64))
    samples=[]
    for _ in range(3):
        raw,result=execute(source,'portableEvents',packed,L['INPUT_WORDS'],L['OUTPUT_WORDS'],backend='metal')
        words=struct.unpack('<'+'I'*(64*L['OUTPUT_WORDS']),raw)
        result['results']=[decode(words[i*L['OUTPUT_WORDS']:(i+1)*L['OUTPUT_WORDS']],program[1]) for i in range(64)]
        assert all(r['status']==0 for r in result['results'])
        assert all(r['queries'][0]['damage']==case['expected_damage'] and r['queries'][0]['combat']['weapons'][0]['ammo']==case['expected_ammo'] for r in result['results'])
        samples.append({k:result[k] for k in ('transport','input_sha256','output_sha256','source_sha256')})
    assert len({r['output_sha256'] for r in samples})==1
    report=dict(strategy='group_rescan' if args.label=='before' else 'indexed_groups',source=source,scope='64 programs, 32 definitions, three seconds of GPU timeline each; not full battle or full catalog',
                passed=True,gpu_execution_verified=True,backend='metal',fixture_sha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
                median_gpu_seconds=statistics.median(r['transport']['gpu_seconds'] for r in samples),samples=samples)
    if args.label=='after':
        before=json.loads((ROOT/'research/portable-quantity-benchmark-before.json').read_text())
        assert before['fixture_sha256']==report['fixture_sha256']
        assert before['samples'][0]['input_sha256']==samples[0]['input_sha256']
        assert before['samples'][0]['output_sha256']==samples[0]['output_sha256']
        report['median_ratio_to_before']=report['median_gpu_seconds']/before['median_gpu_seconds']
    (ROOT/f'research/portable-quantity-benchmark-{args.label}.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'}))


if __name__=='__main__':main()
