"""Audit all real catalog definitions through shared owned/growth preparation.
No GPU execution, support enabling, fake effects, or CPU battle trace.
"""
import hashlib,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter
from detail_coverage import body_for


def main():
    rows=[]
    for name,data in adapter.META.items():
        if not isinstance(data,dict) or name.startswith(('_','test_')) or adapter.spec.is_preview(name):continue
        names=[name]+[n for n in ('모더니아','루주','마스트 : 로망틱 메이드','도라','얀') if n!=name][:4]
        try:row=adapter.evaluate({**body_for(names), '_audit_portable':True})
        except (Exception,SystemExit) as e:row=dict(character=name,setup_error=str(e),full_character_verified=False)
        rows.append(row)
    issues=Counter(e['issue'] for r in rows for e in r.get('effects',[]) if not e['preflight_passed'])
    semantic=Counter(e['diagnostic_semantic_issue'] for r in rows for e in r.get('effects',[]) if e.get('diagnostic_semantic_issue'))
    families=Counter(e['family'] for r in rows for e in r.get('effects',[]) if not e['preflight_passed'])
    weapons=Counter(g for r in rows for g in r.get('weapon_gaps',[]))
    tracked=['app/portable_removal_specs.py','scripts/portable_removal_oracle.py','tests/fixtures/portable-removal.json','app/portable_lifesteal_reference.py','scripts/portable_lifesteal_oracle.py','scripts/portable_landing_oracle.py','tests/fixtures/portable-lifesteal-prototype.json','tests/fixtures/portable-landings.json','app/portable_staged_specs.py','app/staged_dot_specs.py','app/staged_dot_runtime.py','tests/fixtures/portable-staged.json','app/portable_source_specs.py','scripts/portable_source_oracle.py','app/periodic_source_specs.py','app/periodic_source_runtime.py','tests/fixtures/portable-sources.json','app/reference_count_runtime.py','app/reference_health_runtime.py','tests/fixtures/portable-reference-scales.json','app/portable_reference_specs.py','app/portable_resource_specs.py','app/portable_resource_decode.py','app/resource_specs.py','tests/fixtures/portable-resources.json','app/portable_catalog.py','app/portable_enemy_specs.py','app/portable_recipient_specs.py','app/portable_weapon_input.py','app/portable_specs.py','app/portable_runtime.py','app/portable_trigger_specs.py','app/portable_damage_specs.py','app/portable_combat.py','app/engine_worker.py',
             'app/effect_spec.py','scripts/audit-portable-catalog.py','scripts/detail_coverage.py',
             'data/engine-effect-overrides.json','research/upstream/nikke-calc-master/data/parsed_nikke.json']
    from effect_spec import COMPAT_LAYERS
    tracked += ['app/engine_compat.py']+['app/'+name+'.py' for name in COMPAT_LAYERS]
    engine=ROOT/'research/upstream/nikke-calc-master'
    tracked += [p.relative_to(ROOT).as_posix() for folder in ('calculator','runner','data') for p in sorted((engine/folder).rglob('*')) if p.suffix in ('.py','.json')]
    tracked=sorted(set(tracked))
    result=dict(catalog_characters=len(rows),audited_characters=sum('setup_error' not in r for r in rows),
                full_character_verified=sum(r['full_character_verified'] for r in rows),
                weapon_input_preflight_passed=sum(r.get('weapon_input_preflight_passed',False) for r in rows),
                own_effect_preflight_passed=sum(r.get('all_effects_preflight_passed',False) for r in rows),
                assumptions='favorite stage 0, no cube, fixed five-member real roster; definition preflight only; not battle compatibility',
                cpu_simulation_executed=False,gpu_execution_performed=False,issues=dict(issues.most_common()),
                diagnostic_semantic_issues=dict(semantic.most_common()),
                missing_families=dict(families.most_common()),weapon_gaps=dict(weapons.most_common()),characters=rows,
                source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked})
    path=ROOT/'research/portable-catalog-readiness.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('catalog_characters','audited_characters','full_character_verified','weapon_input_preflight_passed','own_effect_preflight_passed','missing_families','weapon_gaps')}))
    if result['audited_characters']!=result['catalog_characters']:raise SystemExit(1)


if __name__=='__main__':main()
