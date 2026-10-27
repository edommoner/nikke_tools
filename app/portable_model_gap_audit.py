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
  game_verified=False,public_admission=False,evidence='research/target-count-query-evidence/metal-physical-lock-cover-v1.json')
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
 return result
