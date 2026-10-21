"""GPU-forbidden native witnesses for the next shared named-magnitude port.

Damage projections prove exercised reference consumers, not full battle/GPU
equivalence. Existing named-state observer cannot yet represent these operators.
"""
import sys,copy,json
from pathlib import Path
from unittest.mock import patch
r=Path(__file__).resolve().parents[1];sys.path[:0]=[str(r/p) for p in ('app','research','scripts')]
from portable_persona_cases import fixtures
from world_projectile_native import observe
from world_enemy_attack_cases import field
import portable_backend,detail_gpu

def verify(output):
    base=copy.deepcopy(fixtures()[0]);base.update(effects=[],owners=[],duration=.8,observe_named_state=False,state_queries=[])
    hit=dict(name='named-hit',source='스킬1',type='damage',stat='damage',fixed_value=100,target='target',trigger=dict(timing=['every:0.2s'],condition=[]))
    rows=[]
    def add(name,effects,owners=None):
     c=copy.deepcopy(base);c.update(name=name,effects=effects,owners=owners or [0]*len(effects));return c
    cases=[add('received-baseline',[field('received_dmg_pct',10,'all_enemies','weakness')]),add('received-amplified',[field('received_dmg_pct',10,'all_enemies','weakness'),field('received_dmg_buff_mag_pct',50,'all_enemies','magnitude',target_effect='weakness')]),add('received-wrong-name',[field('received_dmg_pct',10,'all_enemies','weakness'),field('received_dmg_buff_mag_pct',50,'all_enemies','magnitude',target_effect='other')]),add('damage-baseline',[hit]),add('damage-amplified',[field('dmg_scale_mag_pct',50,'self','magnitude',target_effect='named-hit'),hit]),add('damage-other-owner',[field('dmg_scale_mag_pct',50,'self','magnitude',target_effect='named-hit'),hit],[1,0])]
    def forbidden(*a,**k):raise AssertionError('GPU forbidden during reference witness')
    with patch.object(portable_backend,'build',forbidden),patch.object(portable_backend,'execute',forbidden),patch.object(detail_gpu,'run',forbidden):
     for c in cases:
      native,_=observe(c);rows.append(dict(name=c['name'],damage=native['damage']))
    by={v['name']:v['damage'] for v in rows}
    assert all(a>b for a,b in zip(by['received-amplified'],by['received-baseline']))
    assert by['received-wrong-name']==by['received-baseline']
    assert by['damage-amplified'][0]>by['damage-baseline'][0]
    assert by['damage-amplified'][1:]==by['damage-baseline'][1:]
    assert by['damage-other-owner']==by['damage-baseline']
    report=dict(passed=True,gpu_calls=0,build_calls=0,reference_only=True,portable_admission_verified=False,full_goal_complete=False,cases=rows)
    output.write_text(json.dumps(report,indent=2)+'\n');return report


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():raise ValueError('Reference report already exists')
    print(json.dumps(verify(args.out)))
