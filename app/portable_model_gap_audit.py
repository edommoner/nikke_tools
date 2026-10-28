"""Bounded source audit for the remaining unmodelled canonical consumers.

This is a source assertion, not a game specification or support certificate.
"""
import ast,hashlib,json
from pathlib import Path
MISSING_STATS=('enemy_movement_disable','force_move','effect_range_pct','effect_target_count_add','lock_on')
MODULES=('calculator/timeline.py','calculator/buff_manager.py','calculator/boss_pattern.py','calculator/damage.py')

def verify(root,overrides=None):
 root=Path(root);base='research/upstream/nikke-calc-master/';overrides=overrides or {};text={}
 for name in (*MODULES,'calculator/aim.py','docs/IMPL-STATUS.md'):
  path=base+name;text[name]=overrides.get(path,(root/path).read_text(encoding='utf-8'))
 strings={name:{n.value for n in ast.walk(ast.parse(text[name])) if isinstance(n,ast.Constant) and isinstance(n.value,str)} for name in MODULES}
 status=text['docs/IMPL-STATUS.md'].splitlines();missing={}
 for stat in MISSING_STATS:
  row=next(line for line in status if line.startswith('| `'+stat+'` |'));assert '❌' in row,'Implementation status changed: '+stat
  readers=[name for name,values in strings.items() if stat in values];assert not readers,'New canonical consumer requires review: '+stat
  missing[stat]=dict(native_consumers=readers,status_row=row,scope=list(MODULES))
  if stat=='lock_on':
   missing[stat].update(consumer_search_scope='Explicit stat-literal readers only; generic named carriers may still exist',generic_named_marker_contract='heavyarms-lock-marker-native',dedicated_spatial_selection_verified=False,target_count_extension_verified=False,
    marker_stack_count_is_not_distinct_target_count=True,unlocked_candidate_exclusion_verified=False)
 missing['effect_range_pct']['declared_named_range_selection']={'suite': 'named-effect-range', 'inputs': 21, 'native_cases': 12, 'rejected_cases': 9, 'original_modifier_cases': 5, 'metal_verified': True, 'independently_audited': True, 'current_cuda_verified': False, 'default_producer_installed': False, 'full_original_profile_verified': False, 'battle_damage_delivery_verified': False, 'selection_consumer_connected': True, 'model': 'named-effect-radial-growth-v1', 'evidence': 'tests/fixtures/named-effect-range-independent-v2.json', 'evidence_sha256': 'c225a25c873f3f97346e36007d4200a480db62de28705f65de3dad3f48cf3d2d', 'in_game_radius_semantics_verified': False, 'scope': 'Final checkpoint of shared events and carriers into declared radial circle/rectangle selection only'}
 missing['effect_range_pct']['declared_original_battle_contract']={'suite': 'named-range-battle-common', 'cases': 4, 'original_roster_definitions': 87, 'original_source_profile': '레이 (가칭)', 'source_profile_is_preview': False, 'cast_snapshot_connected': True, 'actual_actor_delivery_connected': True, 'gpu_wire_connected': False, 'metal_verified': False, 'current_cuda_verified': False, 'default_producer_installed': False, 'scope': 'Declared radial growth and canonical logical candidate order; inspect CPU reference report for execution evidence'}
 contract_path='tests/fixtures/heavyarms-lock-published-contract.json'
 contract_raw=overrides.get(contract_path,(root/contract_path).read_text(encoding='utf-8'))
 contract=json.loads(contract_raw)
 assert contract['schema']=='heavyarms-lock-published-contract-v1'
 assert contract['evidence_kind']=='third_party_published_skill_text' and contract['evidence_is_instructions'] is False and contract['in_game_validation_performed'] is False
 assert contract['selection']==dict(interval_seconds=0.2,requires_charging=True,rank='nearest_to_crosshair',exclude_existing_locks=True)
 assert contract['target_capacity']==dict(ordinary_distinct_targets=5,burst_additional_targets=10)
 assert contract['clear_events']==['normal_attack','taking_cover'] and len(contract['unresolved_rules'])==5
 definitions_path=base+'data/parsed_skills.json'
 definitions=json.loads((root/definitions_path).read_text(encoding='utf-8'))[contract['source_profile']['name']]
 assert contract['source_profile']==dict(name='스노우 화이트 : 헤비암즈',definition_count=25,marker_index=0,target_count_index=20,projectile_damage_index=24)
 assert len(definitions)==25 and definitions[0]['stat']=='lock_on' and definitions[0]['max_stack']==5
 assert definitions[20]['stat']=='effect_target_count_add' and definitions[20]['fixed_value']==10 and definitions[20]['duration_bullets']==2
 assert definitions[20]['target_effect']==definitions[0]['name'] and definitions[24]['target']=='all_projectiles'
 missing['lock_on']['published_skill_contract']=dict(fixture=contract_path,sha256=hashlib.sha256(contract_raw.encode()).hexdigest(),source=contract['source'],
  evidence_kind=contract['evidence_kind'],in_game_validation_performed=False,selection=contract['selection'],target_capacity=contract['target_capacity'],clear_events=contract['clear_events'],unresolved_rules=contract['unresolved_rules'])
 missing['effect_target_count_add']['declared_query_reader']=dict(path='app/effect_target_count_policy.py',model='named-effect-target-count-v1',reference_suite='heavyarms-target-count-native',selection_consumer_connected=False,gpu_supported=False)
 missing['effect_target_count_add']['declared_shared_query_executor']=dict(suite='named-target-count-query',native_cases=6,rejected_cases=3,
  source='gpu/effect_target_count_entry.slang',metal_verified=True,independently_audited=True,cuda_verified=False,
  physical_shot_lifetime_verified=False,selection_consumer_connected=False,original_full_profile_verified=False,
  evidence='research/target-count-query-evidence/metal-shared-query-v1.json')
 missing['effect_target_count_add']['declared_physical_shot_query']=dict(suite='named-target-count-shots',native_cases=5,rejected_cases=4,
  original_modifier_definition_cases=2,derived_timing_and_recipient_cases=3,admitted_targets=['self','all_allies'],
  metal_verified=True,independently_audited=True,cuda_verified=False,physical_shot_lifetime_verified=True,
  whole_battle_and_skill_trace_compared=True,all_shots_compared=True,trace_capacity=100,
  selection_consumer_connected=False,original_full_profile_verified=False,
  evidence='research/target-count-query-evidence/metal-physical-shots-v1.json')
 missing['lock_on']['declared_shared_membership_executor']=dict(suite='named-generation-locks',native_cases=10,rejected_cases=6,
  source='gpu/world_generation_locks_entry.slang',metal_verified=True,independently_audited=True,cuda_verified=False,
  actual_world_actor_pools=True,actor_capacity=128,admitted_actor_kinds=['BODY','PART','ADD'],
  provider_order='explicit existing frozen actor set; no distance ranking',named_capacity_reader_connected=True,
  modifier_fixture='original index20 derived to finite time; physical two-shot composition remains separate',
  charging_events_connected=False,spatial_selection_verified=False,sequential_delivery_connected=False,
  game_verified=False,original_full_profile_verified=False,public_admission=False,
  evidence='research/target-count-query-evidence/metal-generation-locks-v1.json')
 missing['lock_on']['declared_physical_membership_executor']=dict(suite='physical-generation-locks',native_cases=6,rejected_cases=4,
  source='gpu/world_physical_locks_entry.slang',metal_verified=True,independently_audited=True,cuda_verified=False,
  separate_lock_arena=True,live_actor_set_capacity=32,queued_full_charge_kill_and_rebirth_verified=True,
  original_index20_preserved=True,physical_two_shot_lifetime_connected=True,native_periodic_charging_connected=True,
  native_on_attack_clear_connected=True,pre_landing_snapshot_connected=True,automatic_cover_clear_verified=False,
  pulse_projection='Original index0 cadence/condition, self marker projection; no nearest-target consumer',
  spatial_selection_verified=False,sequential_delivery_connected=False,original_full_profile_verified=False,game_verified=False,
  public_admission=False,evidence='research/target-count-query-evidence/metal-physical-lock-arena-v2.json')
 missing['lock_on']['declared_physical_cover_composition']=dict(suite='physical-lock-cover',native_cases=11,rejected_cases=12,
  source='gpu/world_physical_lock_cover_entry.slang',metal_verified=True,independently_audited=True,cuda_verified=False,
  shared_manual_control_producer=True,automatic_cover_clear_verified=True,
  owner_scoped_cover_tag=True,full_manual_posture_compared=True,live_actor_set_capacity=32,
  input_words=104400,output_words=806912,extra_wire_words=0,
  spatial_selection_verified=False,sequential_delivery_connected=False,original_full_profile_verified=False,
  game_verified=False,public_admission=False,evidence='research/target-count-query-evidence/metal-physical-lock-cover-v1.json',
  current_source_recertification='research/target-count-query-evidence/metal-cache-preclaim-cover23-v1.json')
 missing['lock_on']['declared_frozen_slot_selector']=dict(suite='lock-delivery-policy',common_policy_cases=46,rejected_cases=17,
  model='cycle-frozen-slot-v1',metal_verified=True,independently_audited=True,cuda_verified=False,
  preserves_typed_generation=True,capacity=128,max_hits=256,compacts_dead_slots=False,
  actual_battle_queue_connected=False,sequential_delivery_connected=False,spatial_selection_verified=False,
  game_verified=False,original_full_profile_verified=False,public_admission=False,
  evidence='research/target-count-query-evidence/metal-lock-delivery-policy-v1.json')
 missing['lock_on']['declared_queued_snapshot_binding']=dict(suite='lock-packet-bindings',native_cases=4,rejected_cases=4,
  source='gpu/world_lock_packet_entry.slang',metal_verified=True,independently_audited=True,cuda_verified=False,
  actual_queue_connected=True,latched_snapshot_and_hit_budget=True,queue_capacity=2048,extra_wire_words=0,
  periodic_snapshot_word_preserved=True,diagnostic_trace_capacity=38,selected_slot_applied_to_landing=False,
  sequential_delivery_connected=False,spatial_selection_verified=False,game_verified=False,
  original_full_profile_verified=False,public_admission=False,
  evidence='research/target-count-query-evidence/metal-lock-packet-bindings-v1.json')
 missing['lock_on']['declared_live_snapshot_delivery']=dict(suite='live-lock-delivery',native_cases=4,rejected_cases=5,
  model='require-live-frozen-slot-v1',source='gpu/world_lock_delivery_entry.slang',
  metal_verified=True,independently_audited=True,cuda_verified=False,
  actual_queue_connected=True,selected_slot_applied_to_landing=True,existing_hp_counter_lifesteal_path=True,
  empty_snapshot_body_fallback=False,dead_missing_stale_policy='reject-unresolved',
  full_sequential_delivery_verified=False,canonical_battle_equivalence=False,
  spatial_selection_verified=False,game_verified=False,original_full_profile_verified=False,public_admission=False,
  evidence='research/target-count-query-evidence/metal-live-lock-delivery-v1.json')
 missing['lock_on']['development_projectile_composition']=dict(suite='lock-projectile-composition',native_cases=5,rejected_cases=4,
  historical=True,source_commit='76b931c68796668ba9247a10194e041f46dc1ddb',superseded_by='declared_projectile_delivery_fates',
  source='gpu/world_lock_projectile_entry.slang',original_index24_preserved=True,single_world_clock=True,
  disjoint_typed_and_lock_arenas=True,resident_runtime_stride_bytes=140008,
  metal_transport_executed=True,metal_verified=False,independently_sealed=False,cuda_verified=False,
  unresolved_comparison='Native suppressed BODY surrogate appears in skill history; actual typed receipts agree. Do not omit history rows.',
  full_profile_verified=False,game_verified=False,public_admission=False,
  evidence='research/target-count-query-evidence/lock-projectile-composition-v1-failure-diagnostic.json')
 missing['lock_on']['declared_projectile_delivery_fates']=dict(suite='lock-projectile-composition',native_cases=7,rejected_cases=5,
  source='gpu/world_lock_projectile_entry.slang',metal_verified=True,independently_sealed=True,cuda_verified=False,
  original_index24_preserved=True,single_world_clock=True,single_receipt_queue=True,
  native_history_rows_preserved=True,explicit_suppressed_body_disposition=True,
  suppressed_receipts_do_not_enter_actor_hp_counter_heal=True,named_and_counter_child_append_order_verified=True,
  disjoint_fate_bank_words=144,typed_targets=128,actor_sets=32,queue_capacity=2048,
  diagnostic_trace_required=True,diagnostic_history_capacity=128,
  spatial_selection_verified=False,dead_retarget_policy_verified=False,full_profile_verified=False,game_verified=False,public_admission=False,
  evidence='research/target-count-query-evidence/metal-packet-fates-v3.json')
 missing['lock_on']['declared_enemy_carrier_executor']=dict(suite='enemy-lock-carriers',native_cases=4,rejected_cases=3,
  source='gpu/world_lock_enemy_carrier_entry.slang',original_indices_preserved=[0,1,2,6,20],
  actual_enemy_carriers=True,existing_actor_carrier_executor=True,empty_dead_carriers_preserved=True,
  metal_verified=True,independently_sealed=True,cuda_verified=False,
  spatial_selection_verified=False,full_profile_verified=False,game_verified=False,public_admission=False,
  evidence='research/target-count-query-evidence/metal-enemy-lock-carriers-v4.json')
 missing['lock_on']['complete_original_roster_composition']=dict(suite='original-lock-composition',native_cases=4,rejected_cases=4,
  source='gpu/world_original_lock_composition_entry.slang',original_source_definitions=25,complete_roster_definitions=91,
  durations_seconds=[3,30],additional_enemies=[0,3],original_weapons_controls_config_preserved=True,
  actual_enemy_marker_sequential_and_projectile_executors_composed=True,
  complete_fraction_team_quota_and_packet_histories=True,preclaim_native_history_budgets=13,
  observed_native_activation_indices=[i for i in range(25) if i!=2],unobserved_native_activation_indices=[2],
  native_activation_evidence='research/target-count-query-evidence/original-lock-native-activation-coverage-v1.json',
  metal_verified=True,independently_sealed=True,cuda_verified=False,
  spatial_selection_verified=False,burst_target_saturation_verified=False,all_conditional_branches_verified=False,game_verified=False,public_admission=False,
  full_profile_verified=False,full_character_certified=False,
  evidence='research/target-count-query-evidence/metal-original-lock-composition-v4.json')
 missing['lock_on']['original_control_and_saturation_composition']=dict(suite='original-lock-controls',native_cases=9,rejected_cases=8,
  source='gpu/world_original_lock_composition_entry.slang',original_source_definitions=25,complete_roster_definitions=91,
  explicit_manual_sequences_applied_after_original_identity_check=True,original_effects_weapons_growth_config_preserved=True,
  cover_source_row=2,actual_enemy_marker_removal_observed=True,cover_empty_and_other_owner_cases=True,
  native_activation_entry_coverage_across_suites=25,native_entry_coverage_is_not_all_branch_certification=True,
  burst_target_saturation_verified=True,burst_distinct_targets=15,burst_uses_before_base_restored=2,
  legacy_cases_retained=8,legacy_output_bytes_retained=41943040,
  metal_verified=True,independently_sealed=True,cuda_verified=False,
  spatial_selection_verified=False,death_retarget_verified=False,parts_and_injury_branches_verified=False,
  all_conditional_branches_verified=False,game_verified=False,public_admission=False,full_character_certified=False,
  evidence='research/target-count-query-evidence/metal-original-lock-controls-v3.json')
 missing['lock_on']['original_parts_and_healing_composition']=dict(suite='original-lock-health-parts',native_cases=7,rejected_cases=4,
  source='gpu/world_original_lock_health_parts_entry.slang',original_source_definitions=25,complete_roster_definitions=91,
  original_effects_weapons_growth_config_preserved=True,formation_variant_declared_as_original_input=True,
  reached_part_actors=2,actual_part_destruction_verified=True,actual_injury_healing_and_cpr_verified=True,
  original_burst_healing_verified=True,hp_condition_true_false_and_later_damage_verified=True,
  existing_healing_diagnostic_rows_compared=204,observed_heal_source_preserved=True,
  hp_and_adjacent_hp_observer_notification_stream_serialized=False,
  early_explicit_entry_wire_gate=True,metal_verified=True,independently_sealed=True,cuda_verified=False,
  lock_part_selection_verified=False,spatial_selection_verified=False,death_retarget_verified=False,
  all_conditional_branches_verified=False,full_profile_verified=False,game_verified=False,public_admission=False,full_character_certified=False,
  evidence='research/target-count-query-evidence/metal-original-health-parts-v2.json')
 missing['effect_target_count_add']['required_consumer_contract']=dict(marker=definitions[0]['name'],additional_targets=10,duration_bullets=2,
  distinct_target_capacity=True,does_not_increase_per_target_marker_stack=True,implementation_verified=False)
 trees={name:ast.parse(text[name]) for name in MODULES}
 functions=lambda name,fn:[n for n in ast.walk(trees[name]) if isinstance(n,ast.FunctionDef) and n.name==fn]
 ranked=functions('calculator/boss_pattern.py','_ranked');assert len(ranked)==1
 assert not any(isinstance(n,ast.Constant) and n.value=='target_and_nearby' for n in ast.walk(ranked[0]))
 assert isinstance(ranked[0].body[-1],ast.Return) and isinstance(ranked[0].body[-1].value,ast.Constant) and ranked[0].body[-1].value.value is None
 helpers=functions('calculator/timeline.py','_resolve_targets');assert len(helpers)==1
 helper=ast.unparse(helpers[0]);assert 'allies = [n for n in names if n in char_states]' in helper and 'return allies' in helper
 handlers=functions('calculator/timeline.py','handle_ammo_charge_pct');assert len(handlers)==1
 body=handlers[0].body;assert any(isinstance(n,ast.For) for n in body)
 last=body[-1];assert isinstance(last,ast.If) and 'bm.notify(' in ast.unparse(last) and 'eff_name' in ast.unparse(last)
 coordinate=functions('calculator/timeline.py','_coord_skill_hits');assert len(coordinate)==1
 selector=next(n for n in coordinate[0].body if isinstance(n,ast.If) and ast.unparse(n.test)=="eff.get('hits_parts')")
 assert ast.unparse(selector.body[0])=="hit = [g for g in geom.targets if g.kind == 'parts']",'Coordinate part-kind selection changed'
 assert any(isinstance(n,ast.Assign) and ast.unparse(n)=="hit = [g for g in geom.targets if g.shape.contains(ax, ay, grow)]" for n in selector.orelse),'Coordinate distance selection changed'
 aim=ast.parse(text['calculator/aim.py'])
 math_calls=sorted({n.func.attr for n in ast.walk(aim) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='math'})
 gate_path='app/portable_world_roster_input.py';gate_text=overrides.get(gate_path,(root/gate_path).read_text(encoding='utf-8'))
 gate=ast.parse(gate_text)
 coordinate_guards=[n for n in ast.walk(gate) if isinstance(n,ast.If) and ast.unparse(n.test)=="enemy.get('coord') is not None and (not coordinate) or enemy.get('part_break_interval', 0)"]
 assert len(coordinate_guards)==1 and any(isinstance(n,ast.Raise) for n in coordinate_guards[0].body),'Coordinate GPU admission changed; update port evidence'
 compiler=next(n for n in gate.body if isinstance(n,ast.FunctionDef) and n.name=='compile_world_battle')
 defaults=dict(zip((n.arg for n in compiler.args.kwonlyargs),compiler.args.kw_defaults))
 assert isinstance(defaults.get('coordinate'),ast.Constant) and defaults['coordinate'].value is False,'Coordinate GPU admission changed; private opt-in must default off'
 literal_guards=[n for n in ast.walk(compiler) if isinstance(n,ast.If) and ast.unparse(n.test)=='type(coordinate) is not bool']
 assert len(literal_guards)==1 and any(isinstance(n,ast.Raise) for n in literal_guards[0].body),'Coordinate GPU admission changed; literal opt-in required'
 public_path='app/engine_worker.py';public_text=overrides.get(public_path,(root/public_path).read_text());public_tree=ast.parse(public_text)
 allowed=[n for n in ast.walk(public_tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='allowed_enemy' for t in n.targets)]
 assert len(allowed)==1 and ast.literal_eval(allowed[0].value)=={'def','code','core_px','distance','has_parts','parts','patterns','optimal_range_weapons'},'Public coordinate admission changed; update port evidence'
 public_guards=[n for n in ast.walk(public_tree) if isinstance(n,ast.If) and ast.unparse(n.test)=='set(enemy) - allowed_enemy']
 assert len(public_guards)==1 and any(isinstance(n,ast.Raise) for n in public_guards[0].body),'Public coordinate admission changed; unknown enemy guard required'
 coordinate_port=dict(classification='gpu_port_gap',native_model_available=True,native_selector='_coord_skill_hits',part_inclusive='all live parts; excludes interrupt; independent of shape distance',ordinary_area='live shape.contains at current aim with pierce/explosion radius',native_math_calls=math_calls,native_pow_operator=any(isinstance(n,ast.BinOp) and isinstance(n.op,ast.Pow) for n in ast.walk(aim)),cpu_contract_suite='coordinate-skill',gpu_connected=False,gpu_rejection_guard_verified=True)
 fixture_path='tests/fixtures/coordinate-native-trig-policy.json';fixture=json.loads((root/fixture_path).read_text())
 assert fixture['source_sha256']==hashlib.sha256(text['calculator/aim.py'].encode()).hexdigest(),'Coordinate numeric source drift requires new host evidence'
 profiles=fixture['observed_profiles'];assert profiles['mac']['contains'] is True and profiles['windows']['contains'] is False
 assert profiles['mac']['sin45_hex']!=profiles['windows']['sin45_hex'] and fixture['common_policy_selected'] is False
 # Above is immutable historical evidence. The user's subsequent selection
 # is separate from implementation and never certifies GPU/public admission.
 decision_path='tests/fixtures/coordinate-common-numeric-decision.json'
 decision_raw=(root/decision_path).read_bytes();decision=json.loads(decision_raw)
 assert decision['schema']==1 and decision['selected_policy']=='deterministic-shared-numeric'
 assert decision['common_policy_selected'] is True and decision['implementation_completed'] is False
 assert decision['contract_id'] is None and decision['public_gpu_admitted'] is False
 coordinate_port['scope']='Public admission and all coordinate policies; private suites remain separate evidence'
 coordinate_port['private_roster_opt_in_available']=True
 coordinate_port['public_enemy_coordinate_rejection_verified']=True
 coordinate_port['numeric_frontend']=dict(classification='gpu_numeric_implementation_gap',host_math_affects_selection=True,common_policy_selected=True,selected_policy=decision['selected_policy'],policy_implemented=False,decision_fixture=decision_path,decision_sha256=hashlib.sha256(decision_raw).hexdigest(),fixture=fixture_path,fixture_sha256=hashlib.sha256((root/fixture_path).read_bytes()).hexdigest(),private_suites=['coordinate-area','coordinate-shape'],private_evidence_does_not_certify_public_admission=True)
 # The historical decision is immutable. Its implementation flag describes
 # public admission, not the subsequently implemented private numeric kernels.
 coordinate_port['numeric_frontend'].update(
  policy_implemented_scope='public coordinate frontend and complete policy admission',
  private_suites=['coordinate-area','coordinate-shape','coordinate-numeric','coordinate-geometry','coordinate-power','coordinate-landing','coordinate-arc-arena','coordinate-landing-arena'],
  private_suite_list_scope='Evidence locations only; inspect each sealed golden and capture before claiming execution coverage',
  resident_integration_suite='coordinate-resident-frames',
  resident_integration_prior_suite='coordinate-resident-arc',
  resident_integration_scope='Private full106 dispatch-frame integration; independent seal in resident-dispatch-frame-evidence/independent106.json',
  resident_frame_metal_verified=True,resident_frame_independently_audited=True,
  resident_frame_cuda_device_verified=False,resident_frame_public_admission_verified=False,
  public_admission_remaining=True)
 result=dict(passed=True,missing_stats=missing,coordinate_world=coordinate_port,target_and_nearby=dict(explicit_ranked_branch=False,fallback='current aimed logical enemy only',nearby_spatial_world=False),enemy_ammo=dict(allied_filter=True,enemy_ammunition_state=False,named_completion_outside_target_loop=True),enemy_healing=dict(allied_heal_consumer_present='heal_received_pct' in strings['calculator/buff_manager.py'],enemy_healing_path_verified=False),historical_documents_are_not_current_instructions=True,gpu_supported=False,full_goal_complete=False,source_sha256={**{base+name:hashlib.sha256(value.encode()).hexdigest() for name,value in text.items()},gate_path:hashlib.sha256(gate_text.encode()).hexdigest(),public_path:hashlib.sha256(public_text.encode()).hexdigest()})
 result['source_sha256'].update({contract_path:hashlib.sha256(contract_raw.encode()).hexdigest(),definitions_path:hashlib.sha256((root/definitions_path).read_bytes()).hexdigest()})
 result['enemy_healing']['declared_source_contract']=dict(suite='enemy-healing-common',cases=6,
  source='app/enemy_healing_model.py',original_profile='앤 : 미라클 페어리',original_definitions=69,
  existing_finite_ADD_health=True,existing_world_source_clock=True,raw_fractional_credit_and_per_owner_rounding=True,
  gpu_wire_connected=False,metal_verified=False,cuda_verified=False,default_path_installed=False,
  scope='Declared CPU reference location; inspect its reference report for execution evidence')
 result['enemy_healing']['declared_metal_validation']={'suite': 'enemy-healing', 'inputs': 14, 'native_cases': 6, 'rejected_cases': 8, 'metal_verified': True, 'independently_audited': True, 'evidence': 'tests/fixtures/enemy-healing-independent-v5.json', 'evidence_sha256': 'e1ad6920d244fd893287b5da1fb56ffeea9203d3db451c2738d45c42b7fb9ad3', 'gpu_wire_connected': True, 'raw_fractional_credit_and_per_owner_rounding': True, 'same_generation_dead_packet_overkill_verified': True, 'current_cuda_verified': False, 'default_producer_installed': False, 'historical_canonical_equivalence': False, 'in_game_rules_verified': False, 'scope': 'Declared source-node finite ADD healing; original Anne 69 definitions, six scenarios only'}
 for path in ('app/enemy_healing_model.py','research/portable_enemy_healing_cases.py','research/portable_enemy_healing_contracts.py','research/world_enemy_healing_native.py'):
  result['source_sha256'][path]=hashlib.sha256((root/path).read_bytes()).hexdigest()
 return result
