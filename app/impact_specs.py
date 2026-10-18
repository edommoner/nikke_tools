"""Typed impact quantities and stable diagnostic wire format.

Credit is independent of damage, critical probability and ammunition. These
types describe an impact; they do not decide which impacts a skill counts.
"""
import math
from dataclasses import dataclass
from enum import IntEnum
from typing import NamedTuple


class ActorKind(IntEnum):
    BODY = 0
    PART = 1
    PROJECTILE = 2
    HP_SHIELD = 3
    HIT_SHIELD = 4
    ADD = 5


class HitFamily(IntEnum):
    WEAPON = 0
    SKILL = 1
    DOT = 2
    EXTERNAL = 3


class HitOutcome(IntEnum):
    MISS = 0
    BLOCKED = 1
    DAMAGING = 2


def enum_value(cls, value):
    if type(value) not in (int, cls):raise ValueError('Invalid impact enum')
    return cls(value)


@dataclass(frozen=True)
class ActorHandle:
    kind: ActorKind
    identity: int
    generation: int = 1

    def __post_init__(self):
        object.__setattr__(self, 'kind', enum_value(ActorKind, self.kind))
        if type(self.identity) is not int or not 0 <= self.identity < 2**28:raise ValueError('Invalid target identity')
        if type(self.generation) is not int or not 1 <= self.generation < 2**31:raise ValueError('Invalid target generation')


@dataclass(frozen=True)
class Impact:
    attacker: str
    target: ActorHandle
    family: HitFamily
    outcome: HitOutcome
    damage: float
    credit: float = 1
    attack_id: int = 0

    def __post_init__(self):
        if not isinstance(self.attacker, str) or not self.attacker:raise ValueError('Invalid impact attacker')
        if not isinstance(self.target, ActorHandle):raise ValueError('Impact requires a target handle')
        object.__setattr__(self, 'family', enum_value(HitFamily, self.family))
        object.__setattr__(self, 'outcome', enum_value(HitOutcome, self.outcome))
        for value in (self.damage, self.credit):
            if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1e30:raise ValueError('Invalid impact quantity')
        if self.outcome != HitOutcome.DAMAGING and self.damage != 0:raise ValueError('Miss/blocked impacts cannot carry damage')
        if self.outcome == HitOutcome.MISS and self.credit != 0:raise ValueError('A miss cannot carry hit credit')
        if type(self.attack_id) is not int or not 0 <= self.attack_id < 2**24:raise ValueError('Invalid attack identity')


class EventFrame(NamedTuple):
    event: str
    caster: str
    time: float
    impact: Impact | None = None
    completion: object = None
    target: ActorHandle | None = None


def inherited_impact(event, parent):
    # Resource/reload/HP notifications intentionally start without a target.
    return parent if inherits_target(event) else None


TARGET_EVENT_PREFIXES = (('hit_count:',8),('event:target_counter_complete:',58))


def inherits_target(event):
    return event=='hit_count' or any(event.startswith(prefix) for prefix,_ in TARGET_EVENT_PREFIXES)


def classify_hit(tag):
    if tag.startswith('dot_damage'):return HitFamily.DOT
    if tag == 'normal_skill':return HitFamily.SKILL
    if tag.startswith(('normal', 'core', 'pellet:', 'full_charge')):return HitFamily.WEAPON
    return HitFamily.SKILL


class ImpactTrace:
    def __init__(self):
        self.count = 0;self.counts = [0] * 24;self.credit = 0.0;self.damage = 0.0
        self.outcomes = [0] * 3;self.last = None;self.time = 0.0

    def record(self, packet, t):
        self.count += 1;self.counts[int(packet.target.kind) * 4 + int(packet.family)] += 1
        self.credit += packet.credit;self.damage += packet.damage
        self.outcomes[int(packet.outcome)] += 1;self.last = packet;self.time = t

    def fields(self, names):
        row = [0.0] * 48;row[0] = self.count;row[1:25] = self.counts
        row[25:27] = [self.credit, self.damage];row[40:43] = self.outcomes
        if self.last:
            p = self.last
            row[27:37] = [int(p.target.kind), p.target.identity, p.target.generation, int(p.family),
                int(p.outcome), names.index(p.attacker), p.damage, p.credit, p.attack_id, self.time]
        else:row[27:30] = [-1, -1, 0]
        return row


def impact_command(t, packet, names):
    """An explicit authored diagnostic impact, never a CPU battle replay."""
    code = int(packet.family) + 4 * int(packet.outcome) + 16 * packet.attack_id
    target = int(packet.target.kind) + 8 * packet.target.identity
    return [t, 8, code, names.index(packet.attacker), target, packet.target.generation, packet.damage, packet.credit]


def decode_command(row, names):
    if any(type(row[i]) not in (int, float) or not math.isfinite(row[i]) or int(row[i]) != row[i] for i in (2, 3, 4, 5)):raise ValueError('Non-integral impact descriptor')
    code, who, target, generation = map(int, (row[2], row[3], row[4], row[5]))
    if not 0 <= who < len(names) or not 0 <= code < 2**28 or not 0 <= target < 2**31:raise ValueError('Invalid impact wire descriptor')
    return Impact(names[who], ActorHandle(target % 8, target // 8, generation), code % 4,
                  (code // 4) % 4, row[6], row[7], code // 16)


def render_cuda():
    lines = ['// Generated from impact_specs.py; do not hand-edit.']
    for prefix, cls in [('ACTOR', ActorKind), ('HIT', HitFamily), ('OUTCOME', HitOutcome)]:
        lines += [f'#define {prefix}_{name} {int(value)}' for name, value in cls.__members__.items()]
    lines.append('struct Impact { int attacker,kind,identity,generation,family,outcome,attack_id; double damage,credit; };')
    return '\n'.join(lines) + '\n'


BEGIN = '// BEGIN GENERATED IMPACT\n'
END = '// END GENERATED IMPACT\n'


def gpu_source_matches():
    from pathlib import Path
    text=Path(__file__).with_name('detail_effects.cu').read_text(encoding='utf-8')
    return text.count(BEGIN)==1 and text.count(END)==1 and text.split(BEGIN)[1].split(END)[0]==render_cuda()
