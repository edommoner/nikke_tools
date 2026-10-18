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
    tracked=['server.mjs','app/engine_worker.py','app/portable_runtime.py','app/portable_backend.py',
             'scripts/verify-portable-api.py','tests/fixtures/portable-events.json',
             'app/portable_combat.py','app/portable_specs.py','app/world_condition_specs.py','app/impact_specs.py',
             'tests/fixtures/portable-combat.json','tests/fixtures/portable-combat-extensions.json']
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
    invalid=copy.deepcopy(payload);invalid['effects'][1]['effect']['stat']='max_hp_pct'
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
    result['extension_execution']=extension_result
    result.update(combat_execution=combat_result,combat_unsupported_status=400,combat_unsupported_error=combat_error)
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    result.update(passed=True,api_status=200,unsupported_status=400,unsupported_error=detail['error'],adapter_sha256=hashes)
    path.write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True,backend=args.backend,device=result['transport']['device'],
                         totals=case['expected_totals'],unsupported_status=400)))


if __name__=='__main__':main()
