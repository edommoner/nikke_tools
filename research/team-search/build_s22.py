"""Add only effect-data-derived burst-state family metadata to frozen profiles."""
import argparse
import copy
import hashlib
import json
from pathlib import Path


def burst_state_family(c,kind):
    # timeline core_damage dispatch and BuffManager runtime self_state gate;
    # only one unambiguous family, with a finite burst-triggered state window.
    family=[e for e in c['effects'] if e.get('type')=='damage' and e.get('stat')==kind]
    if kind!='core_damage' or not family:return False
    for effect in family:
        conditions=effect.get('trigger',{}).get('condition',[])
        gates=[v.removeprefix('self_state:') for v in conditions if v.startswith('self_state:')]
        if not gates:return False
        if not any(any(marker.get('name')==name and marker.get('target')=='self'
                       and marker.get('trigger',{}).get('timing')==['burst_cast']
                       and not marker.get('trigger',{}).get('condition')
                       and isinstance(marker.get('duration'),(int,float)) and marker['duration']>0
                       and marker.get('max_stack',1)==1 for marker in c['effects']) for name in gates):return False
    return True


def effect_bounds(profiles,body):
    """Plain max_stack1 scalar bounds, BuffManager._get_value:5018–5063.

    Exclude all scaling and globally named-amplifiable effects, including the
    profiling context's amplifiers. Levels come from the actual S1 input.
    """
    chars=profiles['characters']
    modified={e.get('target_effect') for c in chars.values() for e in c['effects']
              if e.get('stat') in ('atk_buff_mag_pct','received_dmg_buff_mag_pct')}
    keys={'atk_pct':'atk_pct','atk_dmg_pct':'atk_dmg_pct','atk_caster_based_pct':'atk_flat',
          'reload_speed_pct':'reload_speed_pct','charge_speed_pct':'charge_speed_pct',
          'received_dmg_pct':'received_dmg'}
    from l2_score import burst_dependent
    result={}
    for name,c in chars.items():
        for index,q in enumerate(c['buffs']):
            d=q['effect'];stat=d.get('stat','')
            if stat not in keys or not burst_dependent(d) or d['name'] in modified:continue
            matches=[e for e in c['effects'] if all(e.get(k)==d.get(k) for k in ('name','stat','source','target','trigger'))]
            if len(matches)!=1:continue
            e=matches[0];source=e.get('source','')
            if e.get('type')!='buff' or e.get('max_stack',1)!=1 or e.get('scaling') or e.get('duration_scaling'):continue
            if source not in ('스킬1','스킬2','스킬3'):continue
            level=body['profile']['chars'][name]['skill_levels'][source[-1]]
            value=e.get('fixed_value')
            if value is None:value=(e.get('values') or {}).get(str(level))
            if value is None or float(value)<=0 or keys[stat] not in q['amount']:continue
            cap=float(value)*(c['base_stats']['atk']/100. if stat=='atk_caster_based_pct' else 1.)
            result[name,index]={keys[stat]:cap}
    return result


def build(profiles,switches,body=None):
    p=copy.deepcopy(profiles)
    p['s22']=dict(version=3,switches=switches,method='profile-only; no detailed truth or fitted coefficients',
                  rules={'16':'cast/refcast * reference phase seconds/current phase seconds; own delta same observed supply',
                         '32':'subtract explicitly observed own supply when existing structural condition fails',
                         '64':'core_damage gated by an unambiguous finite burst_cast self state scales with personal casts',
                         '128':'plain max_stack1 effect means cannot exceed their game-data pointwise value; scaling/named amplifications excluded'})
    for c in p['characters'].values():
        for g in c['groups']:g['cast_scaled_s22']=burst_state_family(c,g['kind'])
    if switches&128:
        if body is None:raise ValueError('Effect bounds require the original profiling body')
        bounds=effect_bounds(profiles,body)
        for (name,index),values in bounds.items():p['characters'][name]['buffs'][index]['caps_s22']=values
        p['s22']['bounds']=dict(entries=len(bounds),body_sha256=hashlib.sha256(json.dumps(body,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest())
    return p


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profiles',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--switches',type=int,required=True)
    parser.add_argument('--body',type=Path)
    a=parser.parse_args()
    body=json.loads(a.body.read_text()) if a.body else None
    if isinstance(body,list):body=body[0]
    a.out.write_text(json.dumps(build(json.loads(a.profiles.read_text()),a.switches,body),ensure_ascii=False,separators=(',',':'))+'\n')
