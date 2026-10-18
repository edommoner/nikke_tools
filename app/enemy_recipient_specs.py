"""Sparse immutable recipient identity, shared by effect storage backends."""
from dataclasses import dataclass
from impact_specs import ActorHandle,ActorKind
from enum import IntEnum

CURRENT_TARGETS=frozenset(('enemy','target','target_body','same_target','enemies_nearest_in_range'))

class EnemySelector(IntEnum):
    LEGACY_BODY=0
    CURRENT=1
    BOSS=2
    ALL=3
    OTHER=4


def selector_for(target):
    if target in CURRENT_TARGETS:return EnemySelector.CURRENT
    if target=='boss':return EnemySelector.BOSS
    if target in ('all_enemies','enemies_in_range'):return EnemySelector.ALL
    return EnemySelector.OTHER


def field_instruction(row):
    return row[4]==4 and (row[1]==4 and not row[241] and not row[242] or row[1]==0 and row[2] in (2,3,12,28))


def mutation_instruction(row):
    return row[4]==4 and (row[1] in (15,20,21,26) or row[1]==1 and row[142]>0)


def recipient_instruction(row):return field_instruction(row) or mutation_instruction(row)


def specialize_static_fields(rows, *, has_add_sources):
    """Omit recipient tracking only when configured sources prove a body-only world."""
    if type(has_add_sources) is not bool:
        raise ValueError('Static-field specialization requires a proven source flag')
    if has_add_sources:return 0
    folded=0
    for row in rows:
        if recipient_instruction(row) and row[48]>0:
            row[48]=0
            folded+=1
    return folded


def validate_gpu_fields(rows,has_adds):
    scoped=any(field_instruction(r) and r[48]>0 for r in rows)
    for row in rows:
        if field_instruction(row):
            if int(row[48])!=row[48] or not 0<=row[48]<=4:raise ValueError('Invalid enemy-field recipient selector')
            if has_adds and row[48]>0 and (row[59]>0 or row[62]>=0 or row[69]>0):raise ValueError('Periodic/bullet/finite-passive enemy fields require a recipient lifecycle binding')
            if has_adds and row[0]<5 and row[48] not in (1,2,3):raise ValueError('Enemy-field target selection requires an explicit recipient policy')
        elif mutation_instruction(row):
            if int(row[48])!=row[48] or not 0<=row[48]<=4:raise ValueError('Invalid enemy-mutation recipient selector')
            if has_adds and row[48] not in (1,2,3):raise ValueError('Enemy mutation requires an explicit recipient policy')
            if has_adds and row[59]>0 and row[258]!=1:raise ValueError('Periodic enemy mutation requires an instant timer binding')
        elif has_adds and row[0]<5 and row[4]==4 and row[258]==0 and not (row[1]==0 and row[2]==87):
            raise ValueError('This enemy-field operation requires a recipient binding')
        if scoped and has_adds and row[1]==18 and row[215]>=0 and field_instruction(rows[int(row[215])]):raise ValueError('Enemy-field initialization requires a recipient lifecycle binding')


def render_cuda():
    lines=['// Generated from enemy_recipient_specs.py; do not hand-edit.']
    lines += [f'#define ENEMY_SELECT_{name} {int(value)}' for name,value in EnemySelector.__members__.items()]
    lines += ['__device__ TargetRef logical_enemy_ref(TargetRef a){return a.kind==1?TargetRef{0,0,1}:a;}',
              '__device__ int enemy_wire(TargetRef a){a=logical_enemy_ref(a);return a.kind+8*a.identity;}',
              '__device__ int same_enemy_ref(TargetRef a,TargetRef b){a=logical_enemy_ref(a);b=logical_enemy_ref(b);return enemy_wire(a)==enemy_wire(b)&&a.generation==b.generation;}']
    return '\n'.join(lines)+'\n'


BEGIN='// BEGIN GENERATED ENEMY RECIPIENTS\n'
END='// END GENERATED ENEMY RECIPIENTS\n'


def gpu_source_matches():
    from pathlib import Path
    source=Path(__file__).with_name('detail_effects.cu').read_text(encoding='utf-8')
    return source.count(BEGIN)==source.count(END)==1 and source.split(BEGIN)[1].split(END)[0]==render_cuda()


def logical_enemy(actor):
    if not isinstance(actor,ActorHandle):raise TypeError('Expected an actor handle')
    if actor.kind==ActorKind.PART:return ActorHandle(ActorKind.BODY,0,1)
    if actor.kind not in (ActorKind.BODY,ActorKind.ADD):raise ValueError('Enemy effect recipient requires an explicit actor policy')
    return actor


@dataclass(frozen=True)
class EnemyRecipient:
    label:str
    actor:ActorHandle

    def __post_init__(self):
        if not isinstance(self.label,str) or not self.label:raise ValueError('Invalid enemy recipient label')
        if logical_enemy(self.actor)!=self.actor:raise ValueError('Recipient must use the logical enemy identity')


@dataclass(frozen=True)
class EnemyRecipients:
    bindings:tuple

    def __post_init__(self):
        object.__setattr__(self,'bindings',tuple(self.bindings))
        if not self.bindings or any(not isinstance(b,EnemyRecipient) for b in self.bindings):raise ValueError('Invalid enemy recipient binding')
        if len({b.label for b in self.bindings})!=len(self.bindings) or len({b.actor for b in self.bindings})!=len(self.bindings):raise ValueError('Duplicate enemy recipient identity')

    def actor_for(self,label):
        return next((b.actor for b in self.bindings if b.label==label),None)
