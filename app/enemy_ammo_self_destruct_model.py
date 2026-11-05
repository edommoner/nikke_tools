"""Opt-in final queued shots; the native scheduler still owns retirement.

This extends the declared magazine contract, not game/default admission.
Only exact AttackHit objects already queued at a canonical self-retirement
may spend their own retired generation's magazine at the same frame.
"""
from contextlib import contextmanager
from unittest.mock import patch
from enemy_ammo_model import EnemyAmmo,enemy_ammo,handle_value,source_label
from impact_specs import ActorKind


class SelfDestructEnemyAmmo(EnemyAmmo):
    allows_self_destruct=True

    def __init__(self,spec):
        super().__init__(spec)
        self.retired_shots={}
        self.data.update(model='declared-enemy-magazine-final-queue-v1',retirements=[])

    def note_retirement(self,boss,run,add,why,t):
        if why!='자폭':return
        from calculator.boss_pattern import AttackSpec
        label=add.id
        view=self.registry.view(ActorKind.ADD,label)
        if boss is not self.boss or not view.alive or view.handle.generation!=run.opens:
            raise ValueError('Self-retirement requires the current live original generation')
        queued=[hit for hit in boss.attacks if isinstance(hit.spec,AttackSpec) and source_label(hit)==label]
        if not queued:raise ValueError('Self-retirement must retain its actual final queue')
        for hit in queued:self.retired_shots[id(hit)]=(hit,view.handle,t)
        self.data['retirements'].append(dict(time=t,label=label,actor=handle_value(view.handle),
            fired=add.fired,queued_indices=[hit.index for hit in queued]))

    def retired_queue_allowed(self,hit,t,key):
        receipt=self.retired_shots.pop(id(hit),None)
        return receipt is not None and receipt[0] is hit and receipt[1]==key and receipt[2]==t


@contextmanager
def self_destruct_enemy_ammo(spec):
    from calculator import timeline
    runtime=SelfDestructEnemyAmmo(spec);original=timeline.BossScript
    class Boss(original):
        def _retire(self,run,add,why,t,events,log=True):
            runtime.note_retirement(self,run,add,why,t)
            return super()._retire(run,add,why,t,events,log)
    with patch.object(timeline,'BossScript',Boss),enemy_ammo(spec,runtime_class=lambda _:runtime) as data:
        yield data
