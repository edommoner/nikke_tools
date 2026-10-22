"""Conservative work routing for observed blockers, never feature admission."""


def reference_readiness(issue):
    result=dict(lane='reference_review',native_consumer='not_audited',contract_coverage='not_indexed',
        gpu_supported=False,gpu_admission_verified=False,full_character_verified=False,
        runtime_validation_performed=False)
    if issue.get('phase')=='effect' and issue.get('kind')=='damage' and issue.get('fields')==['hits_parts']:
        result.update(lane='native_contract_extension',native_consumer='confirmed_source',
            consumer_source='research/upstream/nikke-calc-master/calculator/timeline.py:_coord_skill_hits,_handle_damage_eff,_reach_hit',
            contract_coverage='recorded_subset',reference_suites=['parts-skill','parts-skill-extended','parts-skill-lifecycle'],recorded_cases=32,reference_model_gap_cases=1,
            note='Non-coordinate packet/accounting contracts only; legacy deferred bonus drops part metadata and named-hit notify. No GPU admission; coordinate/interrupt world adapters remain separate constraints')
        return result
    if issue.get('phase')!='effect' or issue.get('kind')!='buff':return result
    stat=issue.get('stat')
    if stat=='heal_split':
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
