"""Local adapter around the pinned upstream evaluator; no account network access."""
from __future__ import annotations
import copy, hashlib, json, math, sys, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / 'research/upstream/nikke-calc-master'
sys.path.insert(0, str(ENGINE))
from runner import sim, spec
from calculator import base_stat, timeline
from scraper import profile_fetch as importer
import engine_compat
engine_compat.install()

MAPPINGS = json.loads((ROOT / 'data/import-mappings.json').read_text(encoding='utf-8-sig'))
META = json.loads((ENGINE / 'data/parsed_nikke.json').read_text(encoding='utf-8'))
RESOURCE_NAMES = importer._load_resource_name_map()
REVISION = '23164e4a88fe46af609cc99b0de38a98313a5f4d'
PARTS = ['머리', '몸통', '팔', '다리']
REQUIRED = ['breakthrough', 'core_enhancement', 'affinity', 'skill_levels', 'equipment', 'equip_skills', 'collection_stage', 'cube']


def merge(base, patch):
    out = copy.deepcopy(base)
    for k, v in patch.items():
        out[k] = merge(out.get(k, {}) if isinstance(out.get(k), dict) else {}, v) if isinstance(v, dict) else copy.deepcopy(v)
    return out


def number(v, lo, hi, label, integer=False):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not lo <= v <= hi or (integer and not isinstance(v, int)):
        raise ValueError(f'{label}: {lo}〜{hi}の' + ('整数' if integer else '数値') + 'を指定してください。')
    return v


def catalog():
    by_name = {v: k for k, v in RESOURCE_NAMES.items()}
    display_path = ROOT / 'data/character-display.json'
    display = json.loads(display_path.read_text(encoding='utf-8-sig')) if display_path.exists() else {}
    chars = []
    for name, m in META.items():
        if name.startswith(('_', 'test_')) or not isinstance(m, dict):
            continue
        rid = by_name.get(name)
        chars.append({'name': name, 'label': MAPPINGS['names'].get(str(rid)) or name,
                      'image': display.get(str(rid), {}).get('image'), 'burst': m.get('burst_stage', '?'), 'weapon': m.get('weapon_type', ''), 'element': m.get('element_code', '')})
    cube_display_path = ROOT / 'data/cube-display.json'
    cube_display = json.loads(cube_display_path.read_text(encoding='utf-8-sig')) if cube_display_path.exists() else {'cubes': []}
    return {'characters': chars, 'cubes': list(spec.CUBES), 'cube_labels': {c['name']['ko']: c['name']['ja'] for c in cube_display['cubes']}, 'revision': REVISION,
            'enemy_presets': enemy_presets(), 'overload': {k: v['values'] for k, v in spec._EQUIP_SKILL_TABLE.items() if not k.startswith('_')}}


def enemy_presets():
    archive=ROOT/'data/raid-presets.json'
    return json.loads(archive.read_text(encoding='utf-8-sig'))['presets'] if archive.exists() else []


def burst_controls(squad, profile, policy):
    if policy not in ('auto', 'rules', 'mast3'):
        raise ValueError('未対応のバースト運用です。')
    controls = {}
    if policy == 'rules':
        # Resolve upstream conditional patterns using actual growth and placement,
        # then copy ONLY burst controls. Manual shooting defaults remain disabled.
        for char in spec.build_squad(squad, profile=spec.load_profile(profile)):
            burst = char.get('control', {}).get('burst')
            if burst:
                controls[char['name']] = {'control': {'burst': copy.deepcopy(burst)}}
    if policy == 'mast3' and '마스트 : 로망틱 메이드' in squad:
        controls['마스트 : 로망틱 메이드'] = {'control': {'burst': {'pattern': '3의 배수'}}}
    return controls


def shooting_controls(squad, profile):
    """Keep shooting defaults independent from the selected burst policy."""
    controls = {}
    for char in spec.build_squad(squad, profile=spec.load_profile(profile)):
        shooting = {k: copy.deepcopy(v) for k, v in char.get('control', {}).items() if k != 'burst'}
        if shooting:
            controls[char['name']] = {'control': shooting}
    return controls


def normalize_growth(name, entry):
    entry = copy.deepcopy(entry)
    none = entry.get('cube', {}).get('name') == '__none__' if isinstance(entry.get('cube'), dict) else False
    if none:
        entry.pop('cube')
    normalized = spec.normalize_growth(name, entry, 'import/scenario', strict=True)
    if none:
        normalized['cube'] = {'name': '__none__', 'level': 0}
    return normalized

def normalize_profile(raw):
    if not isinstance(raw, dict) or not isinstance(raw.get('chars'), dict) or not raw['chars']:
        raise ValueError('chars に所持キャラを含む育成JSONが必要です。')
    profile = {'base': 'ungrown', '_account': copy.deepcopy(raw.get('_account') or {}), 'chars': {}}
    warnings, unknown = [], []
    for name, entry in raw['chars'].items():
        if name not in META:
            unknown.append(name)
            continue
        if not isinstance(entry, dict):
            raise ValueError(f'{name}: 育成項目はオブジェクトで指定してください。')
        try:
            profile['chars'][name] = normalize_growth(name, entry)
        except SystemExit as exc:
            raise ValueError(str(exc)) from None
    if not profile['chars']:
        raise ValueError('対応するキャラがありません。キャラ名はエンジンの正式名が必要です。')
    if unknown:
        warnings.append('未対応キャラ（計算対象外）: ' + ', '.join(unknown))
    if raw.get('base') == 'default':
        warnings.append('既定育成を前提にしたJSONです。未記入項目は補完せず、確認が必要な項目として扱います。')
    return {'profile': profile, 'warnings': warnings, 'unknown': unknown,
            'source': 'profile', 'is_demo': bool(raw.get('_meta', {}).get('is_demo'))}


def import_raw(raw):
    for key in ('characters', 'details', 'state_effects'):
        if not isinstance(raw.get(key), list):
            raise ValueError(f'BlaBlaLink JSONの {key} がありません。')
    opt, unknown_opt, off_table = importer._build_option_map(raw['state_effects'], importer._load_equip_skill_table())
    eff = {c['name_code']: c for c in raw['characters']}
    favorites = {int(k): tuple(v) for k, v in MAPPINGS['favorites'].items()}
    cubes = importer._load_cube_name_map()
    weapons = importer._load_weapon_map()
    fav_chars = importer._load_favorite_chars()
    entries, warnings, unknown = {}, [], []
    for detail in raw['details']:
        code = detail.get('name_code')
        name = RESOURCE_NAMES.get(MAPPINGS['id_map'].get(str(code)))
        if name not in META:
            unknown.append(str(code)); continue
        if code not in eff:
            warnings.append(f'{name}: 所持一覧と詳細の対応が取れないため除外しました。'); continue
        try:
            local_warnings = []
            entry = importer._to_profile(detail, eff[code], opt, favorites, name, weapons.get(name), local_warnings, name in fav_chars)
            if local_warnings:
                warnings.extend(local_warnings)
                entry['_import_issues'] = local_warnings
            unknown_slots = [str(detail.get(f'{part}_equip_option{i}_id', 0)) for part, _ in importer.PARTS for i in (1, 2, 3)
                             if detail.get(f'{part}_equip_option{i}_id', 0) and str(detail[f'{part}_equip_option{i}_id']) not in opt]
            if unknown_slots:
                entry['_import_issues'] = ['未知のオバロID: ' + ', '.join(unknown_slots)]
            cube_name = cubes.get(detail.get('harmony_cube_tid'))
            if detail.get('harmony_cube_tid') == 0:
                entry['cube'] = {'name': '__none__', 'level': 0}
            if cube_name:
                entry['cube'] = {'name': cube_name, 'level': detail['harmony_cube_lv']}
            entry['_observed_level'] = eff[code].get('lv')
            observed_power = eff[code].get('combat_power')
            if isinstance(observed_power, (int, float)) and not isinstance(observed_power, bool) and math.isfinite(observed_power) and observed_power >= 0:
                entry['_observed_combat_power'] = observed_power
            entries[name] = entry
        except (KeyError, ValueError, TypeError) as exc:
            warnings.append(f'{name}: 項目不足のため詳細を再取得してください（{exc}）。')
    console_warnings = []
    outpost = raw.get('outpost') or {}
    console = importer._console(outpost.get('recycle_room_researches') or [], console_warnings)
    account = {'synchro_level': outpost.get('synchro_level'), 'cubes': importer._observed_cubes(raw['details'], cubes)}
    if console is not None:
        account['console'] = console
    if unknown_opt or off_table:
        warnings.append('未対応または対応表と一致しないオバロがあります。取り込み情報を確認してください。')
        for entry in entries.values():
            entry['_import_issues'] = entry.get('_import_issues', []) + ['オバロ対応表との不一致を確認してください。']
    result = normalize_profile({'chars': entries, '_account': account})
    result.update(source='blablalink', warnings=warnings + console_warnings, unknown=unknown)
    if unknown:
        result['warnings'].append('未対応のキャラID: ' + ', '.join(unknown))
    missing_details = set(eff) - {d.get('name_code') for d in raw['details']}
    if missing_details:
        result['warnings'].append(f'詳細未取得の所持キャラが{len(missing_details)}人います。')
    return result


def import_data(raw):
    if not isinstance(raw, dict):
        raise ValueError('JSONのトップレベルはオブジェクトが必要です。')
    result = import_raw(raw) if 'characters' in raw else normalize_profile(raw)
    result['snapshot_id'] = hashlib.sha256(json.dumps(result['profile'], sort_keys=True).encode()).hexdigest()
    result['missing'] = missing_fields(result['profile'])
    return result


def missing_fields(profile):
    missing = {}
    account_console = profile.get('_account', {}).get('console')
    for name, entry in profile['chars'].items():
        keys = [k for k in REQUIRED if k not in entry]
        if 'favorite_stage' not in entry and name in importer._load_favorite_chars():
            keys.append('favorite_stage')
        console = entry.get('console') or account_console or {}
        for key, bucket in [('common_level', ''), ('class_level', META[name].get('class')), ('company_level', META[name].get('manufacturer'))]:
            value = console.get(key)
            if value is None or isinstance(value, dict) and bucket not in value:
                keys.append('console.' + key)
        if isinstance(entry.get('equipment'), dict):
            keys += [f'equipment.{p}' for p in PARTS if p not in entry['equipment']]
            for p, gear in entry['equipment'].items():
                if not gear or gear.get('tier') not in ('없음', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8') and 'level' not in gear:
                    keys.append('equipment.' + p + '.level')
        skills = entry.get('skill_levels', {})
        if isinstance(skills, dict):
            keys += [f'skill_levels.{i}' for i in ('1', '2', '3') if i not in skills]
        opts = entry.get('equip_skills', {})
        if isinstance(opts, dict):
            keys += [f'equip_skills.{k}' for k in importer.EQUIP_KEYS if k not in opts]
        keys += entry.get('_import_issues', [])
        if keys:
            missing[name] = keys
    return missing


def demo(expanded=False):
    names = ['리틀 머메이드', '크라운', '라피 : 레드 후드', '헬름', '앨리스']
    if expanded:
        names = [n for n in META if not n.startswith(('_', 'test_')) and not spec.is_preview(n)]
    fields = spec.GROWTH_KEYS
    chars = {n: {k: copy.deepcopy(v) for k, v in spec.DEFAULT_CHAR.items() if k in fields} for n in names}
    for i,(name,entry) in enumerate(chars.items()):
        entry['breakthrough']=i%4
        entry['core_enhancement']=(i//4)%8 if i%4==3 else 0
        entry['affinity']=1+(i*7)%30
        entry['skill_levels']={'1':1+(i*3)%10,'2':1+(i*7)%10,'3':1+(i*9)%10}
        entry['cube']['level']=15-i%15
        entry['favorite_stage']=i%4
        entry['_observed_level']=200+(i*31)%401
        entry['_observed_combat_power']=40000+(i*15437)%280000
        for gear in entry['equipment'].values(): gear['level']=i%6
    chars['크라운']['skill_levels'] = {'1': 7, '2': 7, '3': 7}
    result = import_data({'chars': chars, '_account': {'console': spec.DEFAULT_CHAR['console']}, '_meta': {'is_demo': True}})
    result['warnings'].append('ソート確認用に凸数・スキル・戦闘力などに差を付けた架空データです。ゲーム内の実測値ではありません。')
    result['squad'] = ['리틀 머메이드', '크라운', '라피 : 레드 후드', '헬름', '앨리스']
    return result



def detail_demo():
    """Fictional owned roster for exercising the normal detailed GPU screen."""
    names = ['모더니아', '루주', '마스트 : 로망틱 메이드', '도라', '맥스웰']
    cubes = [n for n, data in spec.CUBES.items() if data['stat'] in ('accuracy_pct', 'charge_speed_pct', 'reload_speed_pct', 'max_ammo_pct')]
    chars = {n: {k: copy.deepcopy(v) for k, v in spec.DEFAULT_CHAR.items() if k in spec.GROWTH_KEYS} for n in names}
    for i, entry in enumerate(chars.values()):
        entry.update(breakthrough=i % 4, core_enhancement=4 if i % 4 == 3 else 0,
                     affinity=1+i*7, skill_levels={'1': 1+i*2, '2': 10-i, '3': 3+i},
                     favorite_stage=0, collection_stage='SR15', cube={'name': cubes[i % len(cubes)], 'level': 1+i*3})
        for gear in entry['equipment'].values(): gear['level'] = i % 6
    chars['루주']['equip_skills'].update(max_ammo_pct=[11.12, 11.12, 12.34], charge_speed_pct=[4.3, 4.3, 6.2])
    result = import_data({'chars': chars, '_account': {'console': spec.DEFAULT_CHAR['console']}, '_meta': {'is_demo': True}})
    result['squad'] = names
    result['warnings'].append('GPU詳細確認用の架空育成です。マクスウェルの有限弾数チャージ武器変更、モダニアの連射武器変更、マストのスタック、装備・キューブを含みます。')
    return result


def evaluate(body):
    profile = copy.deepcopy(body['profile'])
    squad = body['squad']
    if not isinstance(squad, list) or len(squad) != 5 or len(set(squad)) != 5:
        raise ValueError('異なる所持キャラを5人選んでください。')
    if any(n not in profile.get('chars', {}) for n in squad):
        raise ValueError('所持していないキャラは編成できません。')
    patches = body.get('patches', {})
    if set(patches) - set(profile['chars']):
        raise ValueError('未所持キャラへの変更はできません。')
    for name, patch in patches.items():
        profile['chars'][name] = merge(profile['chars'][name], patch)
    for name in squad:
        profile['chars'][name] = normalize_growth(name, profile['chars'][name])
    missing = missing_fields(profile)
    selected_missing = {n: missing[n] for n in squad if n in missing}
    if selected_missing:
        raise ValueError('取り込み情報が不足しています: ' + json.dumps(selected_missing, ensure_ascii=False))
    duration = number(body.get('duration', 180), 1, 180, '戦闘時間')
    level = number(body.get('level', 400), 1, 1000, '戦闘レベル', integer=True)
    for name in squad:
        profile['chars'][name]['level'] = level
    # Do not carry paths, credentials or arbitrary upstream request fields across the boundary.
    profile = {'base': 'ungrown', 'chars': {n: profile['chars'][n] for n in squad},
               '_account': {'console': profile.get('_account', {}).get('console', {})}}
    enemy = body.get('enemy', {})
    allowed_enemy = {'def', 'code', 'core_px', 'distance', 'has_parts', 'parts', 'patterns', 'optimal_range_weapons'}
    if set(enemy) - allowed_enemy:
        raise ValueError('未対応のボス条件です。')
    from detail_world import prepare_enemy,read_parts,cpu_parts_state
    parts=read_parts(enemy.get('parts',[]))
    enemy=prepare_enemy(enemy)
    # The pinned runner schema predates timeline patterns. Validate our fixed
    # factory pattern separately, then attach it after scalar request validation.
    part_patterns=enemy.pop('patterns',[])
    if part_patterns:
        from detail_boss import validate_patterns
        validate_patterns(part_patterns)
    shooting_policy = body.get('shooting_policy', 'auto')
    if shooting_policy not in ('auto', 'character'):
        raise ValueError('射撃運用は完全オートまたはキャラ別の既定操作です。')
    mode_swap=body.get('weapon_mode_swap',False)
    if type(mode_swap) is not bool:raise ValueError('モード用リロードの指定は真偽値です。')
    gauge_mode=body.get('burst_gauge_mode','fixed')
    if gauge_mode not in ('fixed','accumulate'):raise ValueError('ゲージ判定は固定周期または実蓄積です。')
    seed=body.get('seed',0)
    if type(seed) is not int or not 0<=seed<=4294967295:raise ValueError('乱数シードは0〜4294967295の整数です。')
    req = {'squad': squad, 'sim': {'duration': duration, 'expected': True, 'seed':seed, 'burst_gauge_mode':gauge_mode}, 'enemy': enemy,
           'operation': {'auto': True}, 'profile': profile, 'profile_level': 'fixed'}
    deltas = body.get('stat_deltas', {})
    if set(deltas) - set(squad):
        raise ValueError('ステータス変更の対象が編成にいません。')
    for name, fields in deltas.items():
        if not isinstance(fields, dict) or set(fields) - {'atk', 'def', 'hp'}:
            raise ValueError('仮ステータスの項目は atk / def / hp です。')
        for key, value in fields.items():
            number(value, 0, 10000000, f'{name}.{key}')
    no_cube = {n for n in squad if profile['chars'][n]['cube'].get('name') == '__none__'}
    for name in no_cube:
        profile['chars'][name]['cube'] = {'name': next(iter(spec.CUBES)), 'level': 1}
    from calculator.buff_manager import BuffManager
    original_effects = BuffManager._make_cube_effects
    def cube_effects(self, name, level):
        return [] if name == '__none__' else original_effects(self, name, level)
    BuffManager._make_cube_effects = cube_effects
    original = base_stat.calc_base_stats
    def changed(char):
        values = original(char)
        if char['name'] in no_cube:
            values = {k: v - base_stat._CUBE['_stats']['1'][k] for k, v in values.items()}
        return {key: value + deltas.get(char['name'], {}).get(key, 0) for key, value in values.items()}
    # Every evaluation runs in a fresh process. Patch both imported references so
    # setup-time target selection and combat use the same hypothetical base stats.
    spec.calc_base_stats = timeline.calc_base_stats = changed
    try:
        requested_policy = body.get('burst_policy', 'auto')
        policy = 'auto' if requested_policy=='mast3' and '마스트 : 로망틱 메이드' not in squad else requested_policy
        controls = shooting_controls(squad, profile) if shooting_policy == 'character' else {}
        controls = merge(controls, burst_controls(squad, profile, policy))
        controls = merge(controls,{name:{'weapon_mode_swap':mode_swap} for name in squad})
        if controls:
            req['chars'] = controls
        run = sim.prepare(req)
        if part_patterns:run.enemy['patterns']=copy.deepcopy(part_patterns)
        for char in run.squad:
            if char['name'] in no_cube:
                char['cube'] = {'name': '__none__', 'level': 1}
        if body.get('_audit_portable'):
            from portable_catalog import audit_prepared
            return audit_prepared(run, changed, body)
        if body.get('_compile_gpu_detail'):
            from detail_gpu import compile_full
            return compile_full(run, changed, body, policy, requested_policy)
        if body.get('_compile_gpu'):
            from gpu_combat import compile_run
            return compile_run(run, changed, body)
        executed = sim.execute(run)
        result = sim.payload(run, executed)
        if parts:result['parts_state']=cpu_parts_state(parts,executed)
        if body.get('enemy',{}).get('patterns'):
            result['boss_patterns']=copy.deepcopy(body['enemy']['patterns'])
            result['boss_timeline']=[dict(time=round(e.t,6),pattern=e.pattern,kind=e.kind,event=e.event,outcome=e.outcome or None) for e in executed.boss_log if e.pattern!='authored-live-parts' and e.event in ('start','end','dispel')]
            if any(p.get('kind')=='attack' or p.get('kind')=='summon' and p.get('spec',{}).get('attack') for p in body['enemy']['patterns']):
                result['incoming_hits']=[dict(time=round(h.t,6),pattern=h.pattern,target=h.target,damage=round(h.damage,6),pierce=bool(h.pierce),decoy=round(h.decoy,6),shield=round(h.shield,6),cover=round(h.cover,6),hp=round(h.hp,6),hp_after=round(h.hp_after,6),down=bool(h.down),by=h.by or '') for h in executed.squad_hits]
        result['burst_policy'] = policy
        result['shooting_policy'] = shooting_policy
        result['weapon_mode_swap'] = mode_swap
        result['burst_gauge_mode'] = gauge_mode
        result['requested_burst_policy'] = requested_policy
        result['burst_patterns'] = copy.deepcopy(run.config.get('burst_pattern', {}))
        result['burst_timeline'] = [{'time': round(event.t, 3), 'event': event.event, 'character': event.caster}
                                    for event in executed.log.burst_log] if executed.log else []
        result['base_stats'] = {c['name']: changed(c) for c in run.squad}
    finally:
        spec.calc_base_stats = timeline.calc_base_stats = original
        BuffManager._make_cube_effects = original_effects
    numerical_overload = any(any(profile['chars'][name].get('equip_skills', {}).get(k) != body['profile']['chars'][name].get('equip_skills', {}).get(k) for k in patch.get('equip_skills', {})) for name, patch in patches.items() if name in squad)
    result['hypothetical'] = numerical_overload or any(any(v != 0 for v in fields.values()) for fields in deltas.values())
    result['engine_revision'] = REVISION
    result['app_warnings'] = ['固定条件の静止ボスを仮定した参考値です。ボス固有パターンと生存は未検証です。']
    result['app_warnings'].extend(getattr(executed,'effect_model_warnings',[]))
    if body.get('enemy',{}).get('patterns'):result['app_warnings'][0]='設定したボス行動で計算した参考値です。実機のギミックや生存の再現は未検証です。'
    if result['requested_burst_policy']=='mast3' and result['burst_policy']=='auto':
        result['app_warnings'].append('マスト：ロマンチックメイドがいないため、3の倍数指定は適用せず全員オートで計算しました。')
    if result['hypothetical']:
        result['app_warnings'].append('仮ステータスを含みます。ゲーム内で可能な育成を示すものではありません。')
    return result


def candidate_scores(body):
    profile = copy.deepcopy(body['evaluation']['profile'])
    for name, patch in body['evaluation'].get('patches', {}).items():
        profile['chars'][name] = merge(profile['chars'][name], patch)
    missing = missing_fields(profile)
    excluded = set(body.get('excluded', []))
    chars, skipped = [], []
    for name, entry in profile['chars'].items():
        if name in excluded: continue
        if name in missing:
            skipped.append(name); continue
        try:
            normalized = normalize_growth(name, entry)
            no_cube = normalized['cube']['name'] == '__none__'
            if no_cube:
                normalized['cube'] = {'name': next(iter(spec.CUBES)), 'level': 1}
            normalized['level'] = number(body['evaluation'].get('level', 400), 1, 1000, '戦闘レベル', integer=True)
            p = {'base': 'ungrown', '_account': profile.get('_account', {}), 'chars': {name: normalized}}
            char = spec.build_char(name, no_layer=True, profile=spec.load_profile(p))
            atk = base_stat.calc_base_stats(char)['atk']
            if no_cube: atk -= base_stat._CUBE['_stats']['1']['atk']
            atk += body['evaluation'].get('stat_deltas', {}).get(name, {}).get('atk', 0)
            meta = META[name]
            potential = atk * meta.get('damage_coeff', 10) * meta.get('fire_rate', 1)
            chars.append({'name': name, 'potential': potential, 'burst': str(meta.get('burst_stage', ''))})
        except (Exception, SystemExit):
            skipped.append(name)
    from runner.snapshot import SQUADS
    available = {c['name'] for c in chars}
    templates = [v['members'] for v in SQUADS.values() if len(v.get('members', [])) == 5 and len(set(v['members'])) == 5 and set(v['members']) <= available]
    return {'characters': chars, 'skipped': skipped, 'templates': templates}

def dispatch(body):
    action = body.get('action')
    if action == 'gpu_probe':
        from gpu_selector import probe
        return probe()
    if action == 'evaluate_portable_events':
        from portable_runtime import evaluate as evaluate_events
        return evaluate_events(body)
    if action == 'select':
        from gpu_selector import select_teams
        return select_teams(body)
    if action == 'candidates': return candidate_scores(body)
    if action == 'catalog': return catalog()
    if action == 'demo': return detail_demo() if body.get('gpu_detail') else demo(body.get('expanded', False))
    if action == 'import': return import_data(body['data'])
    if action == 'evaluate': return evaluate(body)
    raise ValueError('Unknown action')


if __name__ == '__main__':
    try:
        result = dispatch(json.load(sys.stdin))
        print(json.dumps(result, ensure_ascii=True, allow_nan=False))
    except (Exception, SystemExit) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=True))
        sys.exit(1)






