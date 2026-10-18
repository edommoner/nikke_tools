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
             'scripts/verify-portable-api.py','tests/fixtures/portable-events.json']
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
    assert hashes=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in hashes}
    result.update(passed=True,api_status=200,unsupported_status=400,unsupported_error=detail['error'],adapter_sha256=hashes)
    path.write_text(json.dumps(result,indent=2)+'\n', encoding='utf-8')
    print(json.dumps(dict(passed=True,backend=args.backend,device=result['transport']['device'],
                         totals=case['expected_totals'],unsupported_status=400)))


if __name__=='__main__':main()
