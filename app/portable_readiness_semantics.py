"""Conservative work routing for observed blockers, never feature admission."""


def reference_readiness(issue):
    result=dict(lane='reference_review',native_consumer='not_audited',contract_coverage='not_indexed',
        gpu_supported=False,gpu_admission_verified=False,full_character_verified=False,
        runtime_validation_performed=False)
    operator=issue.get('operator')
    operator=operator if isinstance(operator,dict) else {}
    if issue.get('phase')=='program' and issue.get('category')=='control' and issue.get('fields')==['focus_aim_physical_interrupt']:
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/timeline.py:_land_target; app/world_actor_runtime.py:ActorRegistry.resolve',
            contract_coverage='reproduced_adapter_rejection',reference_suites=['focus-aim'],
            required_extensions=['typed_interrupt_actor_bridge','typed_landing_credit'],
            note='Pinned landing supports interrupt targets, but the current typed comparison bridge rejects their identity. Keep physical admission closed; this is an adapter extension, not an inert effect or an alias for part/projectile credit')
        return result
    if issue.get('phase')=='effect' and issue.get('kind')=='buff' and issue.get('category')=='trigger' and operator.get('domain')=='condition' and operator.get('descriptor') in ('no_broken_cover_ally','focusing'):
        focus=operator['descriptor']=='focusing'
        reader_pending=focus and issue.get('stat') not in ('atk_pct','focus_fire')
        result.update(lane='native_contract_extension' if reader_pending else 'reference_review',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_condition_ok,_runtime_condition_ok,cover_alive,_alive,get_buffs',
            contract_coverage='recorded_subset',reference_suites=['state-predicates']+(['focus-aim'] if focus else []),recorded_cases=15,
            scoped_gpu_suite='state-focus',scoped_metal_validation_performed=True,
            required_extensions=['numeric_query_reader_cache_contract'] if reader_pending else [],
            note='Shared cover/camera predicates and focus presence/aim are connected in scoped Metal cases. Numeric dictionary camera eligibility differs from selective live reads; audit the remaining stat consumers/cache invalidations before broad promotion. Full character support remains unverified')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='recipient' and issue.get('kind') in ('buff','instant'):
        import re
        if re.fullmatch(r'allies_(?:broken_cover_)?random:[1-5]',str(issue.get('target',''))):
            result.update(lane='reference_review',native_consumer='confirmed_source',
                consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_resolve_target_raw,_resolve_lazy',
                contract_coverage='recorded_subset',reference_suites=['ally-random'],recorded_cases=18,scoped_metal_cases=20,
                scoped_gpu_suite='ally-random-gpu',scoped_metal_validation_performed=True,
                required_extensions=[],
                note='Connected shared allied RNG and lazy/eager recipients; scoped Metal20 contracts only. An old recipient diagnostic now needs context review; mixed revival/random, ordered random buff lists and full characters remain unverified')
            return result
    if issue.get('phase')=='program' and issue.get('category')=='control' and issue.get('fields')==['weapon_mode_swap']:
        result.update(lane='reference_review',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/timeline.py:CharState.tick; calculator/buff_manager.py:manual_swap_ready',
            contract_coverage='recorded_subset',reference_suites=['manual-swap','manual-swap-rosters'],recorded_cases=26,
            note='Known mode-swap subset has a separate shared Metal proof; this issue alone does not identify an unported valid control. Review malformed input or combined policies without inferring admission')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='trigger' and issue.get('kind')=='buff' and issue.get('target')=='self' and issue.get('operator')==dict(domain='condition',descriptor='self_undying'):
        result.update(lane='reference_review',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_condition_ok,has_live_stat,_live',
            contract_coverage='recorded_subset',reference_suites=['undying-predicate','undying-predicate-rosters'],recorded_cases=25,
            note='Known explicit-activation subset has separate shared Metal proof with22 authored and3 whole Makima inputs. Review passive/context/malformed issues; this diagnostic alone does not identify an unported valid predicate')
        return result
    if issue.get('phase')=='effect' and issue.get('category')=='trigger' and issue.get('kind')=='buff' and issue.get('target')=='self' and issue.get('operator')==dict(domain='condition',descriptor='self_stat_above:accuracy_pct:0'):
        result.update(lane='reference_review',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_condition_ok',
            contract_coverage='recorded_subset',reference_suites=['accuracy-predicate','accuracy-predicate-rosters'],recorded_cases=28,
            note='Known activation stat-query subset has separate shared Metal proof with26 authored and2 whole profiles. Review the current context/malformed issue without inferring full admission')
        return result
    if issue.get('phase')=='effect' and issue.get('kind')=='damage' and issue.get('fields')==['hits_parts']:
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/timeline.py:_coord_skill_hits,_handle_damage_eff,_reach_hit',
            contract_coverage='recorded_subset',reference_suites=['parts-skill','parts-skill-extended','parts-skill-lifecycle'],recorded_cases=32,reference_model_gap_cases=1,
            note='Non-coordinate packet/accounting contracts only; legacy deferred bonus drops part metadata and named-hit notify. No GPU admission; coordinate/interrupt world adapters remain separate constraints')
        return result
    if issue.get('phase')=='effect' and issue.get('kind')=='instant' and issue.get('stat')=='squad_ammo_consume_as':
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/buff_manager.py:_dispatch_instant',
            contract_coverage='recorded_subset',reference_suites=['ammo-equivalent'],recorded_cases=25,
            note='Literal caster quantity, finite bounded lowering domain; native truncation/extra notices/recursion/tick contracts only, not GPU admission or full-profile certification')
        if issue.get('category')=='effect' and not issue.get('fields') and issue.get('scaling') is None and issue.get('target')=='self':
            result['lane']='gpu_lowering_candidate'
        return result
    if issue.get('phase')!='effect' or issue.get('kind')!='buff':return result
    stat=issue.get('stat')
    if stat=='received_dmg_split':
        result.update(lane='reference_model_gap',native_consumer='specification_deferred_in_pinned_source',
            consumer_source='research/upstream/nikke-calc-master/docs/IMPL-STATUS.md:received_dmg_split',
            note='Differential allocation ratios are undefined in the pinned specification; self_cover and actor delivery are both deferred. Do not alias to received_dmg_split_even or accept as no-op')
    elif stat=='heal_split':
        result.update(native_consumer='declared_cpu_model',consumer_source='app/heal_sharing_compat.py',
            contract_coverage='recorded_subset',reference_suites=['heal-share','heal-share-extended','heal-share-targets','heal-share-lifesteal'],recorded_cases=43,
            lane='native_contract_extension',note='Declared model choices still need in-game confirmation; contracts are not exhaustive')
        if issue.get('category')=='effect' and not issue.get('fields') and issue.get('scaling') is None and issue.get('target') in ('self','all_allies'):
            result['lane']='gpu_lowering_candidate'
    elif stat in ('projectile_dmg_pct','shield_dmg_pct'):
        result.update(lane='native_consumer_research',native_consumer='unconfirmed',
            note='No confirmed consumer in this audit; unchanged output alone does not prove absent semantics')
    elif stat=='cover_def_pct':
        from effect_spec import SCOPED_INERT
        if stat in SCOPED_INERT:
            result.update(lane='reference_model_gap',native_consumer='scoped_inert_in_current_model',
                consumer_source='app/effect_spec.py:SCOPED_INERT',note='Clarify incoming-cover semantics before GPU lowering')
    return result


def work_lanes(priorities):
    """Indexes into the unchanged frequency ranking; no predicted unlock counts."""
    lanes={name:[] for name in ('gpu_lowering_candidate','native_contract_extension','native_consumer_research','reference_model_gap','reference_review')}
    for index,row in enumerate(priorities):lanes[row['reference_readiness']['lane']].append(index)
    return lanes
