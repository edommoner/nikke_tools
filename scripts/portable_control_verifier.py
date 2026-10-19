"""One whole-readback control comparison for either GPU backend.

Only shader selection changes. Packing, expectations and independent native
observers remain the original common combat verifier's implementation.
"""
import argparse,hashlib,importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import portable_runtime


def verify_control(source, stem, entry_script):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backend',choices=('metal','cuda'),default='metal')
    args=parser.parse_args()
    path=ROOT/f'research/portable-combat-{args.backend}.json'
    production_bytes=path.read_bytes();production=json.loads(production_bytes)
    assert production['passed'] and production['gpu_execution_verified'] and production['backend']==args.backend
    assert not production.get('summary_only'), 'Run the common verifier first; a full readback is required'
    reference_path=ROOT/f'research/{stem}-reference-{args.backend}.json'
    spec=importlib.util.spec_from_file_location('portable_control_combat_verifier',ROOT/'scripts/verify-portable-combat.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    execute=portable_runtime.execute;argv=sys.argv
    def control(shader,*values,**options):
        assert shader=='gpu/event_runtime.slang'
        return execute(source,*values,**options)
    try:
        portable_runtime.execute=control;sys.argv=[entry_script,'--backend',args.backend]
        verifier.main()
        reference=json.loads(path.read_bytes());assert reference['passed']
    finally:
        portable_runtime.execute=execute;sys.argv=argv
        if path.exists():reference_path.write_bytes(path.read_bytes())
        path.write_bytes(production_bytes)
    keys=['input_sha256','output_sha256','actual_statuses','expected_statuses','batch_layout','cases','rejected_cases',
          'known_cpu_differences','known_health_cpu_differences','known_mode_cpu_differences']
    keys += [key for key in production if key.endswith('_cpu_regressions')]
    for key in keys:assert production[key]==reference[key],key
    for file,sha in production['source_sha256'].items():assert reference['source_sha256'][file]==sha,file
    tracked=[Path(__file__).resolve(),Path(entry_script).resolve()]
    summary=dict(passed=True,backend=args.backend,gpu_execution_verified=True,positive_cases=len(production['cases']),rejections=len(production['rejected_cases']),
        input_sha256=production['input_sha256'],output_sha256=production['output_sha256'],all_words_equal=True,
        production_source=production['source_sha256'],reference_source=reference['source_sha256'],
        validation_sha256={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked},
        reports=[path.name,reference_path.name],scope='Every authored positive/negative program, all output bytes, all native comparison lists; not full character certification')
    suffix='' if args.backend=='metal' else '-cuda'
    (ROOT/f'research/{stem}-equivalence{suffix}.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:summary[key] for key in ('passed','backend','positive_cases','rejections','all_words_equal')}))
