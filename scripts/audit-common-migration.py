"""Before/after bytecode and acceptance audit for all existing catalog contexts.

Compilation only; this never calls CPU/GPU battle simulation.
"""
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'scripts')]
import detail_gpu
from detail_coverage import coverage

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()

def audit():
    calls=[]
    original=detail_gpu.compile_effects
    def capture(chars,effects):
        try:
            program=original(chars,effects)
        except Exception as exc:
            calls.append({'characters':[c['name'] for c in chars],'error':str(exc)})
            raise
        calls.append({'characters':[c['name'] for c in chars],'program_sha256':digest(program)})
        return program
    detail_gpu.compile_effects=capture
    try:
        normal=coverage()
        spec=importlib.util.spec_from_file_location('migration_inventory',ROOT/'scripts/audit-detail-support.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        variants=module.audit()
    finally:
        detail_gpu.compile_effects=original
    return {'standard':normal,'favorite_matrix':variants['favorite_stage_matrix'],
            'favorite_accepted':variants['accepted_contexts'],'favorite_total':variants['total_contexts'],
            'compiler_calls':calls,'raw_definition_sha256':variants['raw_definition_sha256']}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',action='store_true');p.add_argument('--output',required=True);p.add_argument('--baseline');args=p.parse_args()
    result=audit()
    if not args.capture:
        baseline=json.loads((ROOT/args.baseline).read_text(encoding='utf-8'))
        assert result==baseline,'Existing catalog acceptance or compiled instruction data changed'
        result={'passed':True,'all_existing_compiled_programs_unchanged':True,
                'standard_accepted':result['standard']['supported'],'standard_total':result['standard']['characters'],
                'favorite_accepted':result['favorite_accepted'],'favorite_total':result['favorite_total'],
                'compiler_calls':len(result['compiler_calls']),'baseline_sha256':digest(baseline),
                'scope':'Compilation migration only; no all-character battle correctness claim.'}
    (ROOT/args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('standard','favorite_matrix','compiler_calls')},ensure_ascii=True))
