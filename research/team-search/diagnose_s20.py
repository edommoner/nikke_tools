"""Summarize paired reference observations; no scoring or truth fitting."""
import argparse
import collections
import json
import pathlib


def summarize(r):
    p = r['profile']
    normal = sum(g['hits'] for g in p['groups'] if g['flags'].get('is_normal_atk') and g['kind'] != 'normal_skill')
    return dict(normal_hits=normal, charge_shots=p['actions'].get('_charge_fire',0),
                reload_starts=p['actions'].get('_start_reload',0),
                reload_finishes=p['actions'].get('_finish_reload',0), casts=p['casts'],
                cycles=p['cycles'], full_burst_seconds=p['phase_seconds'][1],
                first_full_burst_times=[e['time'] for e in p['burst_timeline'] if e['event']=='full_burst 시작'][:8],
                methods=p['method_stats'], instant_counts=dict(collections.Counter(e['stat'] for e in p['instant_events'])),
                target_damage=sum(g['damage'] for g in p['groups'])+sum(p['uncovered'].values()))


def run(observations, out):
    rows = [json.loads(p.read_text()) for p in sorted((observations/'runs').glob('*.json'))]
    byid = {r['selection']['id']:r for r in rows}
    assert len(byid) == 221
    comparisons = []
    for r in rows:
        if r['selection']['context'] != 'controlled':
            continue
        control = byid[r['selection']['control_id']]
        a,b = summarize(control),summarize(r)
        comparisons.append(dict(character=r['selection']['target'], intervention=r['selection']['intervention'],
            control_id=control['selection']['id'], intervention_id=r['selection']['id'], control=a, intervention_result=b,
            deltas={k:b[k]-a[k] for k in ('normal_hits','charge_shots','reload_starts','reload_finishes','casts','cycles','full_burst_seconds','target_damage')}))
    result = dict(reference_bodies=len(rows), reference_calls=2*len(rows),
        payload_equalities=sum(r['non_interference'] and r['payload_digest']==r['baseline_digest'] for r in rows),
        landed_hits=sum(r['profile']['landed_hits'] for r in rows),
        summed_plain_seconds=sum(r['baseline_seconds'] for r in rows),
        summed_logged_seconds=sum(r['logged_seconds'] for r in rows), comparisons=comparisons,
        note='One intervention changes a complete teammate or priority. It establishes that package effect, not an independent causal percentage for each of its co-occurring buffs.')
    out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--observations',type=pathlib.Path,required=True)
    p.add_argument('--out',type=pathlib.Path,required=True)
    a=p.parse_args();run(a.observations,a.out)
