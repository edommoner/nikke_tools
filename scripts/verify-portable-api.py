"""Verify the application HTTP -> Python -> shared GPU event path locally."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
import engine_worker
from timer_registry_cases import NAMES


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--url',default='http://127.0.0.1:4317')
    parser.add_argument('--backend',choices=('metal','cuda'),default='metal')
    args=parser.parse_args();url=urllib.parse.urlsplit(args.url)
    if url.scheme!='http' or url.hostname not in ('127.0.0.1','localhost') or url.username or url.password or url.path not in ('','/') or url.query or url.fragment:
        parser.error('Use a loopback HTTP origin')
    path=ROOT/f'research/portable-api-{args.backend}.json'
    path.write_text(json.dumps(dict(passed=False,gpu_execution_verified=False,stage='execution-pending'))+'\n', encoding='utf-8')
    tracked=['app/portable_status_specs.py','scripts/portable_status_oracle.py','tests/fixtures/portable-status.json','app/portable_stack_specs.py','scripts/portable_stack_oracle.py','tests/fixtures/portable-stacks.json','app/portable_duration_extend_specs.py','scripts/portable_duration_extend_oracle.py','tests/fixtures/portable-duration-extend.json','app/portable_removal_specs.py','tests/fixtures/portable-removal.json','app/portable_lifesteal_reference.py','scripts/portable_lifesteal_oracle.py','scripts/portable_landing_oracle.py','tests/fixtures/portable-lifesteal-prototype.json','tests/fixtures/portable-landings.json','app/portable_staged_specs.py','app/staged_dot_specs.py','app/staged_dot_runtime.py','tests/fixtures/portable-staged.json','app/portable_source_specs.py','scripts/portable_source_oracle.py','app/periodic_source_specs.py','app/periodic_source_runtime.py','tests/fixtures/portable-sources.json','app/reference_count_runtime.py','app/reference_health_runtime.py','tests/fixtures/portable-reference-scales.json','app/portable_reference_specs.py','tests/fixtures/portable-hit-references.json','app/portable_resource_specs.py','app/portable_resource_decode.py','app/resource_specs.py','tests/fixtures/portable-resources.json','server.mjs','app/engine_worker.py','app/portable_runtime.py','app/portable_trigger_specs.py','app/portable_damage_specs.py','app/portable_backend.py',
             'scripts/verify-portable-api.py','tests/fixtures/portable-events.json',
             'tests/fixtures/portable-event-candidates.json','tests/fixtures/portable-enemy-attack-ranks.json','tests/fixtures/portable-enemy-spawn-order.json','tests/fixtures/portable-enemy-auto-aim.json','tests/fixtures/portable-periodic-targets.json','tests/fixtures/portable-enemy-buffs.json','tests/fixtures/portable-buff-notices.json','tests/fixtures/portable-mode-sessions.json','tests/fixtures/portable-ammo-modes.json','tests/fixtures/portable-ammo-instants.json','tests/fixtures/portable-burst-duration.json','tests/fixtures/portable-pending-burst.json','tests/fixtures/portable-cover.json','tests/fixtures/portable-enemy-damage.json','tests/fixtures/portable-burst-resources.json','tests/fixtures/portable-bullets.json','tests/fixtures/portable-lazy.json','tests/fixtures/portable-carriers.json','app/portable_recipient_specs.py','tests/fixtures/portable-recipients.json','app/portable_combat.py','app/portable_specs.py','app/portable_periodic_specs.py','app/world_condition_specs.py','app/impact_specs.py',
             'tests/fixtures/portable-capacity.json','tests/fixtures/portable-incoming.json','tests/fixtures/portable-hp-edges.json','tests/fixtures/portable-health.json','tests/fixtures/portable-charge-control.json','tests/fixtures/portable-quantities.json','tests/fixtures/portable-weapons.json','tests/fixtures/portable-damage.json','tests/fixtures/portable-combat.json','tests/fixtures/portable-combat-extensions.json','tests/fixtures/portable-autonomous.json']
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    case=json.loads((ROOT/'tests/fixtures/portable-events.json').read_text(encoding='utf-8'))['cases'][0]
    payload=dict(chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES],
                 effects=[dict(effect=e,owner=NAMES[0]) for e in case['effects']],script=case['script'],
                 base_atk=case['base_atk'],environment=case['environment'],backend=args.backend)
    def request(body):
        req=urllib.request.Request(args.url.rstrip('/')+'/api/portable-events',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=660 if args.backend=='metal' else 120) as response:return json.load(response)
    result=request(payload)
    assert result['gpu_execution_verified'] and result['backend']==args.backend
    assert result['application_event_runtime_connected'] and not result['autonomous_battle_connected']
    assert [sum(q['damage']) for q in result['results'][0]['queries']]==case['expected_totals']
    invalid=copy.deepcopy(payload);invalid['effects'][1]['effect']['stat']='shield_from_max_hp_pct'
    try:request(invalid)
    except urllib.error.HTTPError as error:
        assert error.code==400
        detail=json.load(error);assert 'Unported buff' in detail['error']
    else:raise AssertionError('Unported effect was accepted')
    combat_case=json.loads((ROOT/'tests/fixtures/portable-combat.json').read_text(encoding='utf-8'))['cases'][0]
    combat_payload=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[0]) for e in combat_case['effects']],
                        script=combat_case['script'],base_atk=[1000]*5,combat=combat_case['combat'],backend=args.backend)
    combat_result=request(combat_payload)
    assert combat_result['gpu_execution_verified'] and combat_result['weapon_burst_target_connected']
    assert not combat_result['autonomous_battle_connected']
    for actual,expected in zip(combat_result['results'][0]['queries'],combat_case['expected_queries']):
        assert actual['damage']==expected['damage']
        for key in ('ammo','shots','reload_until','next'):
            assert actual['combat']['weapons'][0][key]==expected['combat']['weapons'][0][key]
    bad_combat=copy.deepcopy(combat_payload);bad_combat['combat']['targets'][0]['kind']=1
    try:request(bad_combat)
    except urllib.error.HTTPError as error:
        assert error.code==400
        combat_error=json.load(error)
    else:raise AssertionError('Unported target kind accepted')
    extension=next(c for c in json.loads((ROOT/'tests/fixtures/portable-combat-extensions.json').read_text(encoding='utf-8'))['cases'] if c['name']=='pellet-callback-mode-switch-keeps-parent-packet')
    extension_payload=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(extension['effects'],extension['owners'])],
                           script=extension['script'],base_atk=[1000]*5,combat=extension['combat'],backend=args.backend)
    extension_result=request(extension_payload)
    assert extension_result['gpu_execution_verified'] and extension_result['weapon_burst_target_connected']
    for actual,expected in zip(extension_result['results'][0]['queries'],extension['expected_queries']):
        assert actual['damage']==expected['damage']
        for key,value in expected['combat']['weapons'][0].items():assert actual['combat']['weapons'][0][key]==value
    timeline_case=next(c for c in json.loads((ROOT/'tests/fixtures/portable-autonomous.json').read_text(encoding='utf-8'))['cases'] if c['name']=='autonomous-180-seconds')
    timeline_payload=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[0]) for e in timeline_case['effects']],
                          script=timeline_case['script'],base_atk=[1000]*5,combat=timeline_case['combat'],backend=args.backend)
    timeline_result=request(timeline_payload)
    assert timeline_result['gpu_execution_verified'] and timeline_result['gpu_timeline_connected']
    assert not timeline_result['autonomous_battle_connected']
    final=timeline_result['results'][0]
    assert final['frames']==10801 and final['queries'][-1]['damage']==[181000,0,0,0,0]
    assert final['targets'][0]['hp']==999819000 and final['targets'][0]['hits']==181
    scalar_case=next(c for c in json.loads((ROOT/'tests/fixtures/portable-damage.json').read_text(encoding='utf-8'))['cases'] if c['name']=='charge-all-seven-factor-order')
    scalar_payload=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[0]) for e in scalar_case['effects']],
                        script=scalar_case['script'],base_atk=[1000]*5,combat=scalar_case['combat'],
                        environment=scalar_case['environment'],backend=args.backend)
    scalar_result=request(scalar_payload)
    assert scalar_result['gpu_execution_verified'] and scalar_result['weapon_burst_target_connected']
    assert scalar_result['results'][0]['queries'][0]['damage']==scalar_case['expected_queries'][0]['damage']
    result['scalar_execution']=scalar_result
    weapon_cases=json.loads((ROOT/'tests/fixtures/portable-weapons.json').read_text(encoding='utf-8'))['cases']
    for name,key in [('unchanged-ratio-reuses-exact-pow','weapon_execution'),('thirty-one-rounds-require-four-clips','reload_execution')]:
        weapon_case=next(c for c in weapon_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[0]) for e in weapon_case['effects']],
                  script=weapon_case['script'],base_atk=[1000]*5,combat=weapon_case['combat'],backend=args.backend)
        actual=request(body)
        assert actual['gpu_execution_verified']
        for a,e in zip(actual['results'][0]['queries'],weapon_case['expected_queries']):assert a['damage']==e['damage']
        if 'expected_final' in weapon_case:
            for k,v in weapon_case['expected_final']['weapons'][0].items():assert actual['results'][0]['weapons'][0][k]==v
        if 'expected_timers' in weapon_case:
            assert actual['results'][0]['timers'][-1]['activations']==weapon_case['expected_timers'][-1]['activations']
        result[key]=actual
    quantity_cases=json.loads((ROOT/'tests/fixtures/portable-quantities.json').read_text(encoding='utf-8'))['cases']
    for name,key in [('integer-capacity-preserves-base-across-large-cancellation','quantity_execution'),('charge-merges-source-before-centisecond-rounding','charge_quantity_execution')]:
        quantity_case=next(c for c in quantity_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[0]) for e in quantity_case['effects']],
                  script=quantity_case['script'],base_atk=[1000]*5,combat=quantity_case['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        for a,e in zip(actual['results'][0]['queries'],quantity_case['expected_queries']):
            assert a['damage']==e['damage']
            for k,v in e.get('combat',{}).get('weapons',[{}])[0].items():assert a['combat']['weapons'][0][k]==v
        result[key]=actual
    malformed=copy.deepcopy(body);malformed['effects'][1]['effect']['_quant_group']={}
    try:request(malformed)
    except urllib.error.HTTPError as error:
        assert error.code==400;quantity_error=json.load(error);assert 'Invalid quantity group' in quantity_error['error']
    else:raise AssertionError('Malformed quantity group accepted')
    charge_case=json.loads((ROOT/'tests/fixtures/portable-charge-control.json').read_text(encoding='utf-8'))['cases'][0]
    charge_body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[0]) for e in charge_case['effects']],
                     script=charge_case['script'],base_atk=[1000]*5,combat=charge_case['combat'],backend=args.backend)
    actual=request(charge_body);assert actual['gpu_execution_verified']
    for a,e in zip(actual['results'][0]['queries'],charge_case['expected_queries']):
        assert a['damage']==e['damage']
        for k,v in e['combat']['weapons'][0].items():assert a['combat']['weapons'][0][k]==v
    assert actual['results'][0]['weapons'][0]['pending_auto_reload'] is True
    assert actual['results'][0]['timers'][-1]['activations']==2
    result['charge_control_execution']=actual
    malformed=copy.deepcopy(charge_body);malformed['combat']['weapons'][0]['cover_during_delay']=1
    try:request(malformed)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'must be boolean' in json.load(error)['error']
    else:raise AssertionError('Malformed charge delay cover policy accepted')
    result['charge_control_unsupported_status']=400
    health_case=json.loads((ROOT/'tests/fixtures/portable-health.json').read_text(encoding='utf-8'))['cases']
    health_case=next(c for c in health_case if c['name']=='heal-recipient-children-finish-before-next-recipient')
    health_body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[0]) for e in health_case['effects']],
                     script=health_case['script'],base_atk=[1000]*5,environment=health_case['environment'],backend=args.backend)
    actual=request(health_body);assert actual['gpu_execution_verified']
    for i,expected in enumerate(health_case['expected_queries'][0]['allies']):
        for k,v in expected.items():assert actual['results'][0]['queries'][0]['allies'][i][k]==v
    result['health_execution']=actual
    malformed=copy.deepcopy(health_body);malformed['environment']['allies'][0]['base_hp']=0
    try:request(malformed)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'Invalid initial ally health' in json.load(error)['error']
    else:raise AssertionError('Invalid initial ally health accepted')
    result['health_unsupported_status']=400
    edge_case=json.loads((ROOT/'tests/fixtures/portable-hp-edges.json').read_text(encoding='utf-8'))['cases']
    edge_case=next(c for c in edge_case if c['name']=='nested-hp-edge-is-suppressed-until-family-finishes')
    edge_body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(edge_case['effects'],edge_case['owners'])],
                   script=edge_case['script'],base_atk=[1000]*5,environment=edge_case['environment'],backend=args.backend)
    actual=request(edge_body);assert actual['gpu_execution_verified']
    assert actual['results'][0]['queries'][0]['attack_buffs']==[0,1,0,0,0]
    assert actual['results'][0]['queries'][0]['allies'][0]['hp']==1000
    result['hp_edge_execution']=actual
    malformed=copy.deepcopy(edge_body);malformed['effects'][1]['effect']['trigger']['timing']=['hp_below_count:50:0']
    try:request(malformed)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'Unported trigger timing' in json.load(error)['error']
    else:raise AssertionError('Invalid HP crossing count accepted')
    result['hp_edge_unsupported_status']=400
    incoming_case=json.loads((ROOT/'tests/fixtures/portable-incoming.json').read_text(encoding='utf-8'))['cases']
    incoming_case=next(c for c in incoming_case if c['name']=='down-notifications-run-after-recipient-cleanup')
    incoming_body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(incoming_case['effects'],incoming_case['owners'])],
                       script=incoming_case['script'],base_atk=[1000]*5,environment=incoming_case['environment'],backend=args.backend)
    actual=request(incoming_body);assert actual['gpu_execution_verified']
    query=actual['results'][0]['queries'][0]
    assert query['attack_buffs']==[0,3,2,2,2]
    assert query['allies'][0]['hp']==0 and query['allies'][0]['down'] is True
    assert query['allies'][0]['received_damage']==2900 and query['allies'][0]['received_hits']==1
    result['incoming_execution']=actual
    malformed=copy.deepcopy(incoming_body);malformed['script'][1][4]=0
    try:request(malformed)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'Invalid incoming body-attack descriptor' in json.load(error)['error']
    else:raise AssertionError('Empty incoming target mask accepted')
    result['incoming_unsupported_status']=400
    capacity_case=json.loads((ROOT/'tests/fixtures/portable-capacity.json').read_text(encoding='utf-8'))['cases']
    capacity_case=next(c for c in capacity_case if c['name']=='timer-state-mask-keeps-high-definition-bits')
    capacity_body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[0]) for e in capacity_case['effects']],
                       script=capacity_case['script'],base_atk=[1000]*5,backend=args.backend)
    actual=request(capacity_body);assert actual['gpu_execution_verified']
    for query,expected in zip(actual['results'][0]['queries'],capacity_case['expected_queries']):
        assert query['active_timer_mask_words']==expected['active_timer_mask_words']
    assert len(actual['results'][0]['timers'])==256
    result['capacity_execution']=actual
    malformed=copy.deepcopy(capacity_body);malformed['effects'].append(copy.deepcopy(malformed['effects'][-1]));malformed['effects'][-1]['effect']['name']='over capacity'
    try:request(malformed)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'capacity' in json.load(error)['error'].lower()
    else:raise AssertionError('257 definitions accepted')
    result['capacity_unsupported_status']=400
    recipient_cases=json.loads((ROOT/'tests/fixtures/portable-recipients.json').read_text(encoding='utf-8'))['cases']
    recipient_evidence=[]
    for name in ('adjacent-heal-owner-first-before-neighbours','empty-casted-recipient-preserves-activation-budget'):
        c=next(c for c in recipient_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],
                  script=c['script'],base_atk=[1000]*5,environment=c['environment'],backend=args.backend)
        if 'combat' in c:body['combat']=c['combat']
        actual=request(body);assert actual['gpu_execution_verified']
        for query,expected in zip(actual['results'][0]['queries'],c['expected_queries']):
            for i,ally in enumerate(expected['allies']):assert query['allies'][i]['hp']==ally['hp']
        if 'expected_timers' in c:assert actual['results'][0]['timers'][0]['activations']==1
        recipient_evidence.append(dict(name=name,execution=actual))
    result['recipient_execution']=recipient_evidence
    carrier_cases=json.loads((ROOT/'tests/fixtures/portable-carriers.json').read_text(encoding='utf-8'))['cases']
    carrier_evidence=[]
    for name in ('eager-target-change-keeps-independent-carriers','same-name-cross-definition-merge-retains-first-value'):
        c=next(c for c in carrier_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],
                  script=c['script'],base_atk=[1000]*5,environment=c['environment'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        assert actual['results'][0]['queries'][0]['attack_buffs']==c['expected_queries'][0]['attack_buffs']
        resident=[x for x in actual['results'][0]['carriers'] if x['active'] and x['effect'] in c['carrier_effect_names']]
        assert len(resident)==len(c['expected_carriers'])
        for a,e in zip(resident,c['expected_carriers']):
            for k,v in e.items():assert a[k]==v
        carrier_evidence.append(dict(name=name,execution=actual))
    result['carrier_execution']=carrier_evidence
    lazy_cases=json.loads((ROOT/'tests/fixtures/portable-lazy.json').read_text(encoding='utf-8'))['cases']
    lazy_evidence=[]
    for name in ('same-caster-time-selector-shares-rank-snapshot','refresh-before-first-consumption-rekeys-pending-sibling','query-freezes-early-condition-before-later-resolution'):
        c=next(c for c in lazy_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],
                  script=c['script'],base_atk=[1000]*5,environment=c['environment'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        for query,expected in zip(actual['results'][0]['queries'],c['expected_queries']):
            assert query['attack_buffs']==expected['attack_buffs']
            for i,ally in enumerate(expected.get('allies',[])):
                for k,v in ally.items():assert query['allies'][i][k]==v
        for k,v in c.get('expected_lazy_cache',{}).items():assert actual['results'][0]['lazy_cache'][k]==v
        lazy_evidence.append(dict(name=name,execution=actual))
    result['lazy_execution']=lazy_evidence
    import importlib.util
    spec=importlib.util.spec_from_file_location('combat_verifier',ROOT/'scripts/verify-portable-combat.py')
    verifier=importlib.util.module_from_spec(spec);spec.loader.exec_module(verifier)
    bullet_cases=json.loads((ROOT/'tests/fixtures/portable-bullets.json').read_text(encoding='utf-8'))['cases']
    bullet_evidence=[]
    for name in ('each-recipient-spends-only-its-own-physical-shots','ten-pellets-two-muzzles-consume-one-budget','recipient-quantity-rounding-uses-independent-stack'):
        c=next(c for c in bullet_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],
                  script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c.get('environment',{}),combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        resident=actual['results'][0]
        verifier.contains(resident['queries'],c['expected_queries'],name)
        if 'expected_carriers' in c:
            live=[x for x in resident['carriers'] if x['active'] and x['effect'] in c['carrier_effect_names']]
            assert len(live)==len(c['expected_carriers']);verifier.contains(live,c['expected_carriers'],name)
        verifier.contains(resident['bullet_lifetimes'],c.get('expected_bullet_lifetimes',dict(active_carriers=len(c['expected_carriers']))),name)
        bullet_evidence.append(dict(name=name,execution=actual))
    result['bullet_execution']=bullet_evidence
    for bad_lifetime in (0,1.5):
        malformed=copy.deepcopy(body);malformed['effects'][1]['effect']['duration_bullets']=bad_lifetime
        try:request(malformed)
        except urllib.error.HTTPError as error:
            assert error.code==400;assert 'bullet lifetime' in json.load(error)['error'].lower()
        else:raise AssertionError('Invalid bullet lifetime accepted')
    result['bullet_unsupported_status']=400
    burst_cases=json.loads((ROOT/'tests/fixtures/portable-burst-resources.json').read_text(encoding='utf-8'))['cases']
    burst_evidence=[]
    for name in ('cooldown-wait-is-recalculated-after-instant','noncasting-b3-receives-each-full-start-2','gauge-allied-instant-25','physical-pellet-gain-and-on-attack-instant-share-gauge'):
        c=next(c for c in burst_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],
                  script=c['script'],base_atk=[1000]*5,combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        burst_evidence.append(dict(name=name,execution=actual))
    result['burst_execution']=burst_evidence
    malformed=copy.deepcopy(body);malformed.pop('combat')
    try:request(malformed)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'requires combat' in json.load(error)['error']
    else:raise AssertionError('Burst modifier accepted without a controller')
    result['burst_unsupported_status']=400
    enemy_cases=json.loads((ROOT/'tests/fixtures/portable-enemy-damage.json').read_text(encoding='utf-8'))['cases']
    enemy_evidence=[]
    for name in ('all-enemies-single-packet','split-clipping-keeps-native-binary64-operation-order','enemy-selector-enemies_top_def-1','respawn-resets-generation-local-scored-health'):
        c=next(c for c in enemy_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],
                  script=c['script'],base_atk=c.get('base_atk',[1000]*5),combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        verifier.contains(actual['results'][0]['trace'],c['expected_packets'],name)
        enemy_evidence.append(dict(name=name,execution=actual))
    result['enemy_execution']=enemy_evidence
    malformed=copy.deepcopy(body);malformed['effects'][1]['effect'].update(stat='dot_damage',tick_interval=.25,duration=1,scaling='stack_count',scaling_ref='unsupported:external:clock:basis')
    try:request(malformed)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'reference' in json.load(error)['error']
    else:raise AssertionError('Unsupported periodic external scaling reference silently accepted')
    result['enemy_unsupported_status']=400
    result['quantity_unsupported_status']=400
    result['timeline_execution']=timeline_result
    result['extension_execution']=extension_result
    result.update(combat_execution=combat_result,combat_unsupported_status=400,combat_unsupported_error=combat_error)
    cover_cases=json.loads((ROOT/'tests/fixtures/portable-cover.json').read_text(encoding='utf-8'))['cases']
    result['cover_execution']=[]
    for name in ('cover-percent-and-flat-order','cover-heal-child-before-next-recipient','cover-revive-then-heal','cover-break-predicate-observes-new-state'):
        c=next(c for c in cover_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c.get('owners',[0]*len(c['effects'])))],script=c['script'],base_atk=[1000]*5,environment=c['environment'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['cover_execution'].append(dict(name=name,execution=actual))
    pending_cases=json.loads((ROOT/'tests/fixtures/portable-pending-burst.json').read_text(encoding='utf-8'))['cases']
    result['pending_execution']=[]
    for name in ('pending-B3-bonus-after-full-start','pending-later-burst-buff-excluded','pending-named-parent-static-repeat','pending-B3-reentry-retains-both-casts'):
        c=next(c for c in pending_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=[1000]*5,combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['pending_execution'].append(dict(name=name,execution=actual))
    duration_cases=json.loads((ROOT/'tests/fixtures/portable-burst-duration.json').read_text(encoding='utf-8'))['cases']
    result['duration_execution']=[]
    for name in ('duration-plus-two','duration-source-is-part-of-identity','duration-freshness-outside-epsilon','duration-full-start-notification-is-after-latch','burst-only-trace-keeps-computation-and-controller-history'):
        c=next(c for c in duration_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=[1000]*5,combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['duration_execution'].append(dict(name=name,execution=actual))
    ammo_cases=json.loads((ROOT/'tests/fixtures/portable-ammo-instants.json').read_text(encoding='utf-8'))['cases']
    result['ammo_execution']=[]
    for name in ('ammo-pct-5-10','ammo-flat--7','ammo-child-after-recipient-deliveries','ammo-negative-partial-reload-recovery','ammo-cancel-does-not-notify-full-reload'):
        c=next(c for c in ammo_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=[1000]*5,combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['ammo_execution'].append(dict(name=name,execution=actual))
    mode_cases=json.loads((ROOT/'tests/fixtures/portable-ammo-modes.json').read_text(encoding='utf-8'))['cases']
    result['infinite_ammo_execution']=[]
    for name in ('sentinel-auto-consumes-cartridge','sentinel-auto-pct-on_attack-maxbuff-False','infinite-buff-presence-0','infinite-cancel-no-completion','infinite-cloned-recipient-carriers'):
        c=next(c for c in mode_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=[1000]*5,combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['infinite_ammo_execution'].append(dict(name=name,execution=actual))
    session_cases=json.loads((ROOT/'tests/fixtures/portable-mode-sessions.json').read_text(encoding='utf-8'))['cases']
    result['mode_session_execution']=[]
    for name in ('mode-entry-is-squad-broadcast','mode-entry-delivers-in-squad-order','mode-transient-entry-cancel-in-last_bullet_fire','mode-pending-cancel-preserves-base-charge','mode-nested-entry-finishes-before-parent-resumes'):
        c=next(c for c in session_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=[1000]*5,combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['mode_session_execution'].append(dict(name=name,execution=actual))
    notice_cases=json.loads((ROOT/'tests/fixtures/portable-buff-notices.json').read_text(encoding='utf-8'))['cases']
    result['named_buff_execution']=[]
    for name in ('buff-audience-None-self','buff-empty-recipients-still-announce-stack-one','buff-lazy-ranked-recipient-order-is-preserved','buff-cancelled-in-name-notice-does-not-grant-health','buff-name-health-child-before-parent-grant'):
        c=next(c for c in notice_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c['environment'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['named_buff_execution'].append(dict(name=name,execution=actual))
    enemy_buff_cases=json.loads((ROOT/'tests/fixtures/portable-enemy-buffs.json').read_text(encoding='utf-8'))['cases']
    result['enemy_buff_execution']=[]
    for name in ('enemy-buff-def_pct-all_enemies','enemy-buff-new-generation-does-not-refresh-old-received_dmg_pct','enemy-buff-notice-scope-recipients','enemy-and-ally-same-name-do-not-merge','enemy-buff-damage-factor-def_caster_based_pct'):
        c=next(c for c in enemy_buff_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c['environment'],combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['enemy_buff_execution'].append(dict(name=name,execution=actual))
    candidate_cases=json.loads((ROOT/'tests/fixtures/portable-event-candidates.json').read_text(encoding='utf-8'))['cases']
    result['event_candidate_execution']=[]
    for name in ('received-count-40','received-count-per-owner-credit','received-count-distinct-thresholds','event-candidate-word-boundaries','event-candidate-force-bypasses-notification-index'):
        c=next(c for c in candidate_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c['environment'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['event_candidate_execution'].append(dict(name=name,execution=actual))
    attack_cases=json.loads((ROOT/'tests/fixtures/portable-enemy-attack-ranks.json').read_text(encoding='utf-8'))['cases']
    result['enemy_attack_execution']=[]
    for name in ('enemy-attack-add-above-body','enemy-attack-packed-eight-high-bit','enemy-attack-multi-hit-reselects-after-kill','enemy-attack-buff-equal-attack-respawn-moves-behind-old-add'):
        c=next(c for c in attack_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c.get('environment',{}),combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['enemy_attack_execution'].append(dict(name=name,execution=actual))
    spawn_cases=json.loads((ROOT/'tests/fixtures/portable-enemy-spawn-order.json').read_text(encoding='utf-8'))['cases']
    result['enemy_spawn_execution']=[]
    for name in ('enemy-spawn-all-warm-then-respawn','enemy-spawn-current-warm-then-respawn','enemy-spawn-nearest-in-range-armor_break_damage','enemy-spawn-buff-nearest'):
        c=next(c for c in spawn_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c.get('environment',{}),combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        if 'expected_packets' in c:
            assert len(actual['results'][0]['trace'])==len(c['expected_packets'])
            verifier.contains(actual['results'][0]['trace'],c['expected_packets'],name+'.packets')
        result['enemy_spawn_execution'].append(dict(name=name,execution=actual))
    aim_cases=json.loads((ROOT/'tests/fixtures/portable-enemy-auto-aim.json').read_text(encoding='utf-8'))['cases']
    result['enemy_auto_aim_execution']=[]
    for name in ('enemy-auto-aim-reverse-birth-nearest-three','enemy-auto-aim-buff-reverse-birth','enemy-auto-aim-weapon-explicit-override','enemy-auto-aim-autonomous-two-shooters'):
        c=next(c for c in aim_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c.get('environment',{}),combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        if 'expected_packets' in c:
            assert len(actual['results'][0]['trace'])==len(c['expected_packets'])
            verifier.contains(actual['results'][0]['trace'],c['expected_packets'],name+'.packets')
        result['enemy_auto_aim_execution'].append(dict(name=name,execution=actual))
    periodic_cases=json.loads((ROOT/'tests/fixtures/portable-periodic-targets.json').read_text(encoding='utf-8'))['cases']
    result['periodic_target_execution']=[]
    for name in ('periodic-target-retirement-and-respawn','periodic-target-named-alias-unions-in-insertion-order','periodic-target-own-stack-scaling','periodic-target-split_damage-delayed'):
        c=next(c for c in periodic_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c.get('environment',{}),combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        assert len(actual['results'][0]['trace'])==len(c['expected_packets'])
        verifier.contains(actual['results'][0]['trace'],c['expected_packets'],name+'.packets')
        result['periodic_target_execution'].append(dict(name=name,execution=actual))
    resource_cases=json.loads((ROOT/'tests/fixtures/portable-resources.json').read_text(encoding='utf-8'))['cases']
    result['resource_execution']=[]
    for name in ('resource-fractional-caps-and-snapshot-boundary-union','resource-modulo-beyond-int64-and-negative-truncation','resource-nested-charge-keeps-parent-snapshot','resource-down-clears-value-keeps-key-and-base-cap'):
        c=next(c for c in resource_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c.get('environment',{}),backend=args.backend)
        if 'combat' in c:body['combat']=c['combat']
        actual=request(body);assert actual['gpu_execution_verified'];resident=actual['results'][0]
        verifier.contains(resident['queries'],c['expected_queries'],name)
        verifier.contains(resident['resource_queries'],c['expected_resource_queries'],name)
        if 'expected_resource_trace' in c:assert resident['resource_trace']==c['expected_resource_trace'],name
        result['resource_execution'].append(dict(name=name,execution=actual))
    reference_cases=json.loads((ROOT/'tests/fixtures/portable-hit-references.json').read_text(encoding='utf-8'))['cases']
    result['hit_reference_execution']=[]
    for name in ('reference-parent-count-before-hit-consumption','reference-first-carrier-not-sum','reference-gauge-reference-overrides-numeric-suffix','reference-periodic-reads-count-at-each-tick'):
        c=next(c for c in reference_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified'];verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['hit_reference_execution'].append(dict(name=name,execution=actual))
    scale_cases=json.loads((ROOT/'tests/fixtures/portable-reference-scales.json').read_text(encoding='utf-8'))['cases']
    result['scale_reference_execution']=[]
    for name in ('scale-first-capture-before-notice-refresh-after-notices','scale-self-reference-first-none-then-refresh','scale-dot-capture-refresh-5','scale-health-root-resource-change-crosses-once'):
        c=next(c for c in scale_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),backend=args.backend)
        if 'combat' in c:body['combat']=c['combat']
        if 'environment' in c:body['environment']=c['environment']
        actual=request(body);assert actual['gpu_execution_verified'];verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['scale_reference_execution'].append(dict(name=name,execution=actual))
    source_cases=json.loads((ROOT/'tests/fixtures/portable-sources.json').read_text(encoding='utf-8'))['cases']
    result['source_execution']=[]
    for name in ('source-population-expiry-and-phase','source-group-owners-before-interleaved-keys','source-damage-legacy','source-health-max_hp_only_pct'):
        c=next(c for c in source_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),backend=args.backend)
        if 'combat' in c:body['combat']=c['combat']
        if 'environment' in c:body['environment']=c['environment']
        actual=request(body);assert actual['gpu_execution_verified'];verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        if 'expected_source_queries' in c:verifier.contains(actual['results'][0]['source_queries'],c['expected_source_queries'],name+'.source_queries')
        if name=='source-damage-legacy':
            from periodic_source_specs import LEGACY_WARNING
            assert LEGACY_WARNING in actual['app_warnings']
        result['source_execution'].append(dict(name=name,execution=actual))
    staged_cases=json.loads((ROOT/'tests/fixtures/portable-staged.json').read_text(encoding='utf-8'))['cases']
    result['staged_execution']=[]
    for name in ('staged-triangular-and-post-period','staged-callback-refresh-invalidates-old-generation','staged-literal-zero-skips-attachment','staged-expired-periodic-source-time'):
        c=next(c for c in staged_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),backend=args.backend,combat=c['combat'])
        if 'environment' in c:body['environment']=c['environment']
        actual=request(body);assert actual['gpu_execution_verified'];verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        from staged_dot_specs import MODEL_WARNING
        assert MODEL_WARNING in actual['app_warnings']
        result['staged_execution'].append(dict(name=name,execution=actual))
    landing_cases=json.loads((ROOT/'tests/fixtures/portable-landings.json').read_text(encoding='utf-8'))['cases']
    result['landing_execution']=[]
    for name in ('landing-native-next-frame','landing-drain-includes-appended-child','landing-split-rounded-recovery','landing-b3-child-pending-survives-parent-drain'):
        c=next(c for c in landing_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c['environment'],combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified'];verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        if 'expected_landing_queue' in c:verifier.contains(actual['results'][0]['landing_queue'],c['expected_landing_queue'],name+'.queue')
        if 'expected_pending_burst' in c:verifier.contains(actual['results'][0]['pending_burst'],c['expected_pending_burst'],name+'.pending')
        from portable_lifesteal_reference import MODEL_WARNING as LIFESTEAL_WARNING
        assert LIFESTEAL_WARNING in actual['app_warnings']
        result['landing_execution'].append(dict(name=name,execution=actual))
    missing_phase=copy.deepcopy(body);missing_phase['environment']['native_landing']=False
    try:request(missing_phase)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'Lifesteal requires native landing phases' in json.load(error)['error']
    else:raise AssertionError('Lifesteal without native receipts was accepted')
    removal_cases=json.loads((ROOT/'tests/fixtures/portable-removal.json').read_text(encoding='utf-8'))['cases']
    result['removal_execution']=[]
    for name in ('removal-target-self','removal-children-recreate-retired-slots','removal-eight-enemy-end-notices','removal-pure-instant-clock-survives-global'):
        c=next(c for c in removal_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c['environment'],combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified'];verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['removal_execution'].append(dict(name=name,execution=actual))
    invalid_scope=copy.deepcopy(body);invalid_scope['effects'][1]['effect']['remove_scope']='unknown'
    try:request(invalid_scope)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'Unknown named removal scope' in json.load(error)['error']
    else:raise AssertionError('Unknown named removal scope was accepted')
    extension_cases=json.loads((ROOT/'tests/fixtures/portable-duration-extend.json').read_text(encoding='utf-8'))['cases']
    result['duration_extend_execution']=[]
    for name in ('duration-extend-shared-instance-whole-expiry','duration-extend-enemy-independent-boss','duration-extend-staged-before-ramp-end','duration-extend-overflow-infinity-is-not-a-large-finite-number'):
        c=next(c for c in extension_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],script=c['script'],base_atk=c.get('base_atk',[1000]*5),environment=c.get('environment',{}),combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified'];verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        result['duration_extend_execution'].append(dict(name=name,execution=actual))
    invalid_extension=copy.deepcopy(body);invalid_extension['effects'][1]['effect']['target_effect']=None
    try:request(invalid_extension)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'Duration extension requires a state name' in json.load(error)['error']
    else:raise AssertionError('Invalid duration extension was accepted')
    session_cases=json.loads((ROOT/'tests/fixtures/portable-mode-sessions.json').read_text(encoding='utf-8'))['cases']
    result['session_identity_execution']=[]
    for name in ('session-identity-end-pct-child-reentry','session-identity-end-pct-child-cancel',
                 'session-identity-old-charge-limit-cannot-end-replacement','session-identity-warmup-shot-keeps-physical-clock'):
        c=next(c for c in session_cases if c['name']==name)
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],c['owners'])],
                  script=c['script'],base_atk=c.get('base_atk',[1000]*5),combat=c['combat'],backend=args.backend)
        actual=request(body);assert actual['gpu_execution_verified']
        verifier.contains(actual['results'][0]['queries'],c['expected_queries'],name)
        if 'expected_final' in c:verifier.contains(actual['results'][0],c['expected_final'],name+'.final')
        result['session_identity_execution'].append(dict(name=name,execution=actual))
    stack_cases=json.loads((ROOT/'tests/fixtures/portable-stacks.json').read_text(encoding='utf-8'))['cases']
    from portable_stack_oracle import compare as compare_stacks
    result['stack_execution']=[]
    for name in ('stack-captured-notices-survive-parent-removal','stack-init-shared-enemy-immunity-is-generation-bound','stack-max-per-target-overrides-rise-at-representative-cap','stack-nested-removal-defers-derived-hp-until-stack-children'):
        c=next(c for c in stack_cases if c['name']==name)
        owners=c.get('owners',[0]*len(c['effects']))
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],owners)],script=c['script'],base_atk=c.get('base_atk',[1000]*5),combat=c['combat'],backend=args.backend)
        if 'environment' in c:body['environment']=c['environment']
        actual=request(body);assert actual['gpu_execution_verified']
        compare_stacks(c,actual['results'][0],verifier.contains)
        result['stack_execution'].append(dict(name=name,execution=actual))
    status_cases=json.loads((ROOT/'tests/fixtures/portable-status.json').read_text(encoding='utf-8'))['cases']
    from portable_status_oracle import compare as compare_status
    result['status_execution']=[]
    for name in ('status-same-name-pools-across-owners','status-recharge-after-all-named-children','status-cleanse-dot-retains-clock-captured-reference','status-cleanse-snapshot-health--10','status-null-and-omitted-state-share-identity'):
        c=next(c for c in status_cases if c['name']==name);owners=c.get('owners',[0]*len(c['effects']))
        body=dict(chars=payload['chars'],effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(c['effects'],owners)],script=c['script'],base_atk=c.get('base_atk',[1000]*5),combat=c['combat'],backend=args.backend)
        if 'environment' in c:body['environment']=c['environment']
        actual=request(body);assert actual['gpu_execution_verified'];compare_status(c,actual['results'][0],verifier.contains)
        result['status_execution'].append(dict(name=name,execution=actual))
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    result.update(passed=True,api_status=200,unsupported_status=400,unsupported_error=detail['error'],adapter_sha256=hashes)
    path.write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True,backend=args.backend,device=result['transport']['device'],
                         totals=case['expected_totals'],unsupported_status=400)))


if __name__=='__main__':main()
