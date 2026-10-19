"""Run every common case with live-sort control and compare all readback bytes.
Only the GPU source selector changes. The original compiler, native observers,
hand expectations, negative table, and input packing are reused unchanged.
"""
import hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_runtime
spec=importlib.util.spec_from_file_location('event_index_reference_verifier',ROOT/'scripts/verify-portable-combat.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)


def main():
    path=ROOT/'research/portable-combat-metal.json';production_bytes=path.read_bytes();production=json.loads(production_bytes)
    assert production['passed'] and production['gpu_execution_verified'] and production['backend']=='metal'
    reference_path=ROOT/'research/portable-attack-rank-reference-metal.json'
    execute=portable_runtime.execute;argv=sys.argv
    def control(source,*args,**kwargs):
        assert source=='gpu/event_runtime.slang'
        return execute('gpu/benchmark_attack_rank_scan.slang',*args,**kwargs)
    try:
        portable_runtime.execute=control;sys.argv=[__file__,'--backend','metal'];v.main()
        reference=json.loads(path.read_bytes());assert reference['passed']
    finally:
        portable_runtime.execute=execute;sys.argv=argv
        if path.exists():reference_path.write_bytes(path.read_bytes())
        path.write_bytes(production_bytes)
    keys=['input_sha256','output_sha256','actual_statuses','expected_statuses','batch_layout','cases','rejected_cases','known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']
    keys += [k for k in production if k.endswith('_cpu_regressions')]
    for key in keys:assert production[key]==reference[key],key
    for file,sha in production['source_sha256'].items():assert reference['source_sha256'][file]==sha,file
    summary=dict(passed=True,backend='metal',gpu_execution_verified=True,positive_cases=len(production['cases']),rejections=len(production['rejected_cases']),
        input_sha256=production['input_sha256'],output_sha256=production['output_sha256'],all_words_equal=True,
        production_source=production['source_sha256'],reference_source=reference['source_sha256'],
        validation_sha256={str(Path(__file__).relative_to(ROOT)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
        reports=['portable-combat-metal.json',reference_path.name],scope='Every authored positive/negative program, all output bytes, all native comparison lists; not full character certification')
    (ROOT/'research/portable-attack-rank-equivalence.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:summary[k] for k in ('passed','positive_cases','rejections','all_words_equal')}))


if __name__=='__main__':main()
