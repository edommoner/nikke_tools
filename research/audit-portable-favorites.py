"""Inspect all203 characters at each favorite stage without battle execution."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'app'), str(ROOT/'scripts')]
import engine_worker as adapter
from detail_coverage import body_for


def main():
    names = [name for name, data in adapter.META.items() if isinstance(data, dict)
             and not name.startswith(('_', 'test_')) and not adapter.spec.is_preview(name)]
    assert len(names) == 203
    rows = []
    for name in names:
        squad = [name]+[n for n in ('모더니아', '루주', '마스트 : 로망틱 메이드', '도라', '얀') if n != name][:4]
        for stage in range(4):
            body = body_for(squad)
            body['profile']['chars'][name]['favorite_stage'] = stage
            row = adapter.evaluate({**body, '_audit_portable': True})
            assert not row['cpu_simulation_executed'] and not row['full_character_verified']
            rows.append(dict(character=name, favorite_stage=stage, own_effects=row['own_effects'],
                all_effects_preflight_passed=row['all_effects_preflight_passed'],
                weapon_input_preflight_passed=row['weapon_input_preflight_passed'],
                weapon_gaps=row['weapon_gaps'],
                unadmitted_effects=[e for e in row['effects'] if not e['preflight_passed']]))
    assert len(rows) == 812
    baseline = json.loads((ROOT/'research/portable-catalog-readiness.json').read_text())
    first = {r['character']: r for r in rows if r['favorite_stage'] == 0}
    for old in baseline['characters']:
        row = first[old['character']]
        for key in ['own_effects', 'all_effects_preflight_passed', 'weapon_input_preflight_passed', 'weapon_gaps']:
            assert row[key] == old[key], (old['character'], key)
        assert row['unadmitted_effects'] == [e for e in old['effects'] if not e['preflight_passed']]
    issues = Counter(e['issue'] for row in rows for e in row['unadmitted_effects'])
    families = Counter(e['family'] for row in rows for e in row['unadmitted_effects'])
    all_stages = [n for n in names if all(r['all_effects_preflight_passed'] for r in rows if r['character'] == n)]
    paths = ['research/audit-portable-favorites.py', 'research/portable-catalog-readiness.json', 'app/portable_catalog.py', 'app/portable_runtime.py',
             'app/portable_roster_input.py', 'app/portable_trigger_specs.py', 'app/portable_probability_specs.py',
             'app/portable_damage_specs.py', 'app/engine_worker.py', 'scripts/detail_coverage.py',
             'research/upstream/nikke-calc-master/calculator/buff_manager.py',
             'research/upstream/nikke-calc-master/data/parsed_nikke.json']
    result = dict(passed=True, catalog_characters=203, audited_contexts=812, stage0_matches_current_audit=True,
        own_effect_preflight_contexts_passed=sum(r['all_effects_preflight_passed'] for r in rows),
        all_four_stages_preflight_characters=len(all_stages), all_four_stages_preflight_names=all_stages,
        cpu_simulation_executed=False, gpu_execution_performed=False, full_character_verified=0,
        scope='Favorite stages0..3,default skill levels,no cube,same fixed five-member squad;preflight only;not GPU support certification',
        issues=dict(issues.most_common()), missing_families=dict(families.most_common()), contexts=rows,
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    (ROOT/'research/portable-favorite-readiness.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print('All812 favorite contexts audited;preflight accepted', result['own_effect_preflight_contexts_passed'],
          ';all4-stage candidates',len(all_stages),';full certification0/203')


if __name__ == '__main__':
    main()
