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
    tracked=['server.mjs','app/engine_worker.py','app/portable_runtime.py','app/portable_trigger_specs.py','app/portable_damage_specs.py','app/portable_backend.py',
             'scripts/verify-portable-api.py','tests/fixtures/portable-events.json',
             'tests/fixtures/portable-cover.json','tests/fixtures/portable-enemy-damage.json','tests/fixtures/portable-burst-resources.json','tests/fixtures/portable-bullets.json','tests/fixtures/portable-lazy.json','tests/fixtures/portable-carriers.json','app/portable_recipient_specs.py','tests/fixtures/portable-recipients.json','app/portable_combat.py','app/portable_specs.py','app/world_condition_specs.py','app/impact_specs.py',
             'tests/fixtures/portable-capacity.json','tests/fixtures/portable-incoming.json','tests/fixtures/portable-hp-edges.json','tests/fixtures/portable-health.json','tests/fixtures/portable-charge-control.json','tests/fixtures/portable-quantities.json','tests/fixtures/portable-weapons.json','tests/fixtures/portable-damage.json','tests/fixtures/portable-combat.json','tests/fixtures/portable-combat-extensions.json','tests/fixtures/portable-autonomous.json']
    hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in tracked}
    case=json.loads((ROOT/'tests/fixtures/portable-events.json').read_text(encoding='utf-8'))['cases'][0]
    payload=dict(chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=engine_worker.META[n]) for n in NAMES],
                 effects=[dict(effect=e,owner=NAMES[0]) for e in case['effects']],script=case['script'],
                 base_atk=case['base_atk'],environment=case['environment'],backend=args.backend)
    def request(body):
        req=urllib.request.Request(args.url.rstrip('/')+'/api/portable-events',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=120) as response:return json.load(response)
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
    malformed=copy.deepcopy(body);malformed['effects'][1]['effect'].update(tick_interval=.25,duration=1)
    try:request(malformed)
    except urllib.error.HTTPError as error:
        assert error.code==400;assert 'per-recipient clocks' in json.load(error)['error']
    else:raise AssertionError('Multi-target periodic damage silently accepted')
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
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    result.update(passed=True,api_status=200,unsupported_status=400,unsupported_error=detail['error'],adapter_sha256=hashes)
    path.write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True,backend=args.backend,device=result['transport']['device'],
                         totals=case['expected_totals'],unsupported_status=400)))


if __name__=='__main__':main()
