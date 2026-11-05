"""Combined owned-data acceptance: real five-member battles, no CPU event replay."""
import argparse,copy,hashlib,importlib.util,json,random,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker as adapter


def fixtures():
    # Fictional owned growth, including gear, overload arrays, cubes, collection,
    # per-character console and account console. Retain every raw character skill.
    base=json.loads((ROOT/'research/detail-charge-immunity-api-fixture.json').read_text(encoding='utf-8'))
    base.update(duration=60,_debug_random_state=True)
    for variant in ('imported','growth-and-stats','reordered'):
        for shooting in ('auto','character'):
            for gauge in ('fixed','accumulate'):
                body=copy.deepcopy(base)
                body.update(shooting_policy=shooting,burst_gauge_mode=gauge,burst_policy='rules')
                if variant=='imported':body.update(patches={},stat_deltas={})
                if variant=='reordered':body['squad']=list(reversed(body['squad']))
                yield f'{variant}-{shooting}-{gauge}',body
    # Exercise automatic candidate choice and the cycle preference using a real
    # alternate B2. The same imported entries are kept when positions change.
    spec=importlib.util.spec_from_file_location('owned_full_fixtures',ROOT/'scripts/verify-full-detail.py')
    full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)
    for policy in ('auto','rules','mast3'):
        for reverse in (False,True):
            body=full.fixture(90,policy,grown=True,reverse=reverse)
            body.update(seed=12345,shooting_policy='character',burst_gauge_mode='accumulate',_debug_random_state=True)
            yield f'mast-{policy}-'+('right' if reverse else 'left'),body




def positive_controls(rows):
    """Parity alone must not pass if owned growth or squad order is ignored."""
    indexed={(r['backend'],r['name']):r for r in rows}
    checks={}
    for backend in sorted({r['backend'] for r in rows}):
        for shooting in ('auto','character'):
            for gauge in ('fixed','accumulate'):
                suffix=f'{shooting}-{gauge}'
                imported=indexed[backend,'imported-'+suffix]
                grown=indexed[backend,'growth-and-stats-'+suffix]
                reordered=indexed[backend,'reordered-'+suffix]
                checks[f'{backend}-{suffix}']={
                    'growth_changes_damage':imported['cpu_total']!=grown['cpu_total'],
                    'positions_change_damage':grown['cpu_total']!=reordered['cpu_total'],
                }
    return checks
