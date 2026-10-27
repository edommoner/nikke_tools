"""Declared geometry extends original sampled battle routing, not its arithmetic."""
import copy,dataclasses
from unittest.mock import patch
import engine_worker
from calculator import timeline
from battle_attack_group_runtime import battle_attack_groups
from coordinate_logical_actor_geometry import logical_actor_geometry
from world_coordinate_sampling_native import common_sampling_policy

def observe(case):
    before=copy.deepcopy(case);body=case['body'];prepared=engine_worker.evaluate(dict(body,_portable_static_inputs=True));captured={};points=[];draws=[]
    original_weapon={c['name']:copy.deepcopy(c['_weapon']) for c in prepared['chars']}
    def execute(run):
        chars=[{k:v for k,v in c.items() if k!='_weapon'} for c in prepared['chars']]
        assert run.squad==chars and run.config==prepared['policies']['config'] and run.seed==prepared['policies']['seed']
        assert {**timeline.DEFAULT_ENEMY,**(run.enemy or {})}==prepared['enemy']
        assert all(timeline._NIKKE[n]==w for n,w in original_weapon.items())
        enemy=copy.deepcopy(run.enemy);enemy.update(coord=copy.deepcopy(case['coord']),patterns=copy.deepcopy(case['patterns']))
        answer=timeline.simulate(run.squad,config=run.config,enemy=enemy,seed=run.seed,verbose=True);captured['result']=answer;return answer
    with battle_attack_groups(routing='native',coordinate_packets=True) as groups,logical_actor_geometry(case['logical_geometry']) as geometry,common_sampling_policy(points,draws),patch.object(engine_worker.sim,'execute',execute):
        engine_worker.evaluate(copy.deepcopy(body))
        captured['physical_rng_state']=copy.deepcopy(timeline.random.getstate())
    assert case==before and len(geometry['managers'])==len(geometry['bosses'])==1
    manager=geometry['managers'][0]
    actual=[dict(effect=e,owner=o) for e,o in manager._effects]
    assert actual==prepared['effects'],'Logical geometry must retain every original effect and owner'
    handle=lambda h:[int(h.kind),h.identity,h.generation]
    field_names={r['effect']['name'] for r in prepared['effects'] if r['owner']=='벨로타' and r['effect'].get('type')=='buff' and any(t.startswith('multi_hit:') for t in r['effect'].get('trigger',{}).get('timing',[]))}
    fields=[dict(name=a.effect['name'],stat=a.effect['stat'],recipients=list(a.target_chars or ()),
        bound_actors=[handle(b.actor) for b in getattr(a,'enemy_recipient_key').bindings] if getattr(a,'enemy_recipient_key',None) is not None else [])
        for a in manager._active if a.effect['name'] in field_names]
    native=dict(battle=dataclasses.asdict(captured['result']),groups=[dict(r,targets=[handle(h) for h in r['targets']]) for r in groups['groups']],
        notices=[dict(owner=r['owner'],event=r['event'],time=r['time'],identity=r['key'].identity,targets=[handle(h) for h in r['targets']]) for r in groups['notifications']],
        receipts=[dict(r,target=handle(r['target'])) for r in groups['physical_receipts']],
        children=[dict(r,targets=[handle(h) for h in r['targets']]) for r in groups['children']],
        child_landings=[dict(r,target=handle(r['target'])) for r in groups['child_landings']],
        logical_shots=geometry['shots'],logical_packets=geometry['packets'],logical_pellet_channels=geometry['pellets'],enemy_group_fields=fields,
        sampled_points=points,physical_draws=draws,physical_rng_state=captured['physical_rng_state'],
        original_input_identity=dict(definitions=len(actual),effects_owners_weapons_chars_config_seed_verified=True,added_effects=0),
        scope='Explicit sampled ADD collider model; original scalar, scheduler, health, layered landing and group executor; not historical canonical battle equivalence or GPU proof')
    return native,native['receipts']
