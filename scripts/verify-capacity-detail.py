"""Effect-ID boundaries and rich, unmodified-skill whole squads against CPU."""
import argparse,copy,hashlib,importlib.util,json,math,random,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import detail_gpu as g
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=load('capacity_counts','scripts/verify-counts-detail.py')
t=load('capacity_team','scripts/verify-team-hits-detail.py')
E=c.E;NAMES=c.NAMES
def fillers(n):
    return [(E('capacity inert '+str(i),'buff','atk_pct',0,event='inactive'),NAMES[0]) for i in range(n)]
def primitives():
    for boundary in (31,32,127,128,255):
        effects=fillers(256)
        effects[boundary]=(E('high reducer','buff','trigger_count_reduce',2,target_effect='high listener'),NAMES[0])
        listener=128 if boundary!=128 else 127
        effects[listener]=(E('high listener','buff','atk_pct',1,event='on_attack_count:5',max_stack=1000),NAMES[0])
        p=c.oracle.program(c.oracle.characters(NAMES),effects)
        assert int(p['effects'][listener][g.REDUCER_MASK+boundary//32])&(1<<(boundary%32))
        assert p['states']['high listener']>=127
        script=[[0,0,0,i,0,-1,0,0] for i in range(5)]+[[(i+1)/10,0,7,0,0,-1,0,0] for i in range(9)]
        script.append([1,2,0,0,p['states']['high listener'],0,0,0])
        yield 'reducer-id-'+str(boundary),p,script,3
    # Expanded attacker definitions must keep shared budgets above the old cap.
    effects=fillers(129)
    source=NAMES[0]
    effects.append((E('high team budget','buff','atk_pct',7,'all_allies',event='body_hit_count:1',max_trigger=3,max_stack=10),source))
    p=c.oracle.program(c.oracle.characters(NAMES),effects)
    assert all(row[269]==130 for row in p['effects'][129:134])
    script=[[0,0,0,i,0,-1,0,0] for i in range(5)]
    for i,attacker in enumerate((4,0,2,3,1,4,0),1):script.append([i/10,0,45,attacker,-1,-1,0,0])
    script.append([1,2,0,0,p['states']['high team budget'],0,0,0])
    yield 'team-shared-budget-id-129',p,script,None
def rich_fixture():
    fixture=json.loads((ROOT/'research/detail-team-hits-api-fixture.json').read_text(encoding='utf-8'))
    previous=json.loads((ROOT/'research/ports/v28/research/detail-capacity-cpu-audit.json').read_text(encoding='utf-8'))['burst_chain_example']
    growth=fixture['profile']['chars'][fixture['squad'][0]]
    body=copy.deepcopy(fixture);body['squad']=[r['character'] for r in previous['characters']]
    body['profile']['chars']={r['character']:{**copy.deepcopy(growth),'favorite_stage':r['favorite']} for r in previous['characters']}
    body.update(patches={},stat_deltas={},duration=31,burst_policy='auto',shooting_policy='character',burst_gauge_mode='accumulate',seed=12345)
    return body
