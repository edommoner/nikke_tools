"""Plan raw geometry input from native evidence;does not enable GPU admission."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from portable_specs import LIMITS as L


def main():
    native = json.loads((ROOT / 'research/portable-core-range-native.json').read_text())
    assert native['passed'] and native['cpu_only'] and not native['gpu_admission_enabled']
    audit = json.loads((ROOT / 'research/portable-catalog-readiness.json').read_text())
    affected = []
    for character in audit['characters']:
        effects = [e for e in character['effects'] if e['stat'] in ('optimal_range_min', 'optimal_range_max_pct')
                   or any(c in ('core_hit', 'optimal_range') for c in e['conditions'])]
        if effects:
            affected.append(dict(character=character['character'], effects=effects,
                                 all_effects_preflight_passed=character['all_effects_preflight_passed']))
    start = L['RECIPIENT_NODE_BASE'] + L['RECIPIENT_NODES'] * 8
    # All offsets here are proposed,not current ABI fields.
    count = 16 + 5 * 8 + L['DEFINITIONS'] * 6
    assert start % 8 == 0 and start + count <= L['INPUT_WORDS']
    paths = ['research/study-geometry-layout.py', 'research/portable-core-range-native.json',
             'research/portable-catalog-readiness.json', 'app/portable_specs.py', 'app/portable_combat.py',
             'app/portable_weapon_input.py', 'app/portable_roster_input.py', 'app/portable_trigger_specs.py',
             'app/portable_damage_specs.py', 'app/detail_gpu.py', 'app/effect_spec.py',
             'research/upstream/nikke-calc-master/calculator/buff_manager.py']
    result = dict(passed=True, design_only=True, gpu_admission_enabled=False, gpu_execution_performed=False,
        current_abi='0x5045566C', input_words=L['INPUT_WORDS'], unused_input_tail_words=L['INPUT_WORDS'] - start,
        proposed_geometry_base=start, proposed_geometry_words=count,
        proposed_remaining_tail_words=L['INPUT_WORDS'] - start - count,
        proposed_sections=dict(world_header=16, five_original_weapons=5*8, mode_geometry=256*6),
        required_literal_inputs=['Enemy core_px as binary64;GPU compares >=1',
            'Distance as binary64 and separate presence flag;do not use a numeric sentinel',
            'Explicit weapon-list membership mask;original weapon IDs for conditions',
            'Original weapon lower/upper range and active-mode lower/upper range',
            'Each active mode also needs its literal weapon ID for distance-absent membership;mode6-word record reserves ID/flags plus two binary64 bounds'],
        required_execution=['Keep original weapon for activation optimal_range predicate',
            'Use current active weapon mode for normal attack damage range bonus',
            'No distance:membership only,no stat query',
            'Distance:one shared stat query preserves lazy recipient resolution side effects',
            'Evaluate authored condition order with probability/stat short circuit',
            'Numeric stat IDs61/62 remain in existing64-entry vector;never treat them as direct damage boosts',
            'Apply binary64 lower=max(0,baseLower*(1-minimumPct/100)),upper=baseUpper*(1+maximumPct/100)',
            'Closed bounds use binary64 lower-1e-9 and upper+1e-9,withoutfloat32',
            'Core/range activation predicates are skipped on runtime buff queries like native',
            'Avoid new Runtime private arrays;read immutable geometry from commands'],
        required_rejections=['Nonfinite core/distance/bounds', 'Invalid masks,owner IDs and range order',
            'Unsupported moving enemy/core world events until their shared execution is implemented'],
        future_verification=['Raw admission negative cases for each new field',
            'Native geometry cases including weapon changes,stat-query ordering and low/high endpoint slack',
            'Range buffs affect actual physical damage as well as predicates',
            'All previous2280 input bytes except ABI and all output words preserved',
            'Include deferred rounding chains [100,99.99999999999999,0] in next shared probability fixture expansion',
            'All current Mac gates and short CUDA verification before measuring the new common geometry helper'],
        affected_characters=affected,
        scope='Proposed complete geometry connection;not implementation or evidence of character compatibility',
        source_sha256={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths})
    (ROOT / 'research/portable-geometry-layout-study.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print('Geometry raw-input layout fits existing stride;affected characters', len(affected))


if __name__ == '__main__':
    main()
