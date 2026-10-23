"""Opt-in physical interrupt receipts, outside canonical ActorKind/Impact.

The native target and lifesteal implementations remain the executors. This
bridge reads their actual pool/accounting state and never aliases kind6 to a
part, body or projectile. Canonical impact consumers receive their old kinds.
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
import math
from unittest.mock import patch

from impact_specs import HitFamily, classify_hit
from portable_interrupt_specs import KIND, pool_bindings


@dataclass(frozen=True)
class InterruptHandle:
    identity: int
    generation: int
    kind: int = field(default=KIND, init=False)

    def __post_init__(self):
        if type(self.identity) is not int or not 0 <= self.identity < 2**28:
            raise ValueError('Invalid private interrupt identity')
        if type(self.generation) is not int or not 1 <= self.generation < 2**31:
            raise ValueError('Invalid private interrupt generation')


@dataclass(frozen=True)
class InterruptSnapshot:
    handle: InterruptHandle
    alive: bool
    hits: int
    dealt: float
    landed: float


class InterruptRegistry:
    def __init__(self, boss):
        self.boss = boss
        self.bindings = {b.label: b for b in pool_bindings([r.p for r in boss._runs]) if int(b.kind) == KIND}
        if len(self.bindings) != sum(len(r.p.targets) for r in boss._runs if r.p.kind == 'interrupt'):
            raise ValueError('Ambiguous private interrupt label')

    def view(self, label):
        try:
            binding = self.bindings[label]
        except KeyError:
            raise ValueError('Unknown private interrupt: ' + str(label)) from None
        run = self.boss._runs[binding.run]
        if run.opens == 0:
            raise ValueError('Private interrupt has not spawned')
        target = run.targets[binding.slot]
        return InterruptSnapshot(InterruptHandle(binding.identity, run.opens),
                                 bool(run.active and not target.destroyed),
                                 target.hits, target.dealt, target.landed)

    def exact(self, handle):
        if not isinstance(handle, InterruptHandle):
            raise TypeError('Private interrupt lookup requires its own handle')
        binding = next((b for b in self.bindings.values() if b.identity == handle.identity), None)
        if binding is None:
            raise ValueError('Unknown private interrupt identity')
        result = self.view(binding.label)
        if result.handle != handle:
            raise ValueError('Stale private interrupt generation')
        return result


@dataclass(frozen=True)
class InterruptReceipt:
    attacker: str
    target: InterruptHandle
    label: str
    time: float
    damage: float
    before: InterruptSnapshot
    after: InterruptSnapshot
    accounted_before: float
    accounted_after: float
    # This is a private landing receipt, never a canonical hit-credit packet.
    canonical_credit: int = field(default=0, init=False)

    def __post_init__(self):
        if not self.attacker or not self.label or not isinstance(self.target, InterruptHandle):
            raise ValueError('Invalid private interrupt receipt')
        if self.before.handle != self.target or self.after.handle != self.target:
            raise ValueError('Private interrupt generation changed within landing')
        for value in (self.time, self.damage, self.accounted_before, self.accounted_after):
            if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
                raise ValueError('Invalid private interrupt quantity')


_active = False


@contextmanager
def capture_interrupt_landings(*, capacity=65536):
    """Explicit private adapter; do not change the default CPU execution path.

    Capture the native hit_target return before the already installed landing
    hook, then consume the same event object there. No additional buff, aim,
    RNG, damage or target-lifecycle query is issued.
    """
    global _active
    if type(capacity) is not int or not 1 <= capacity <= 65536:
        raise ValueError('Invalid private interrupt receipt capacity')
    if _active:
        raise RuntimeError('Private interrupt capture cannot be nested')
    from calculator.boss_pattern import BossScript
    from calculator.buff_manager import BuffManager
    native_hit, native_landing = BossScript.hit_target, BuffManager.publish_landing
    receipts, pending, registries = [], {}, {}

    def hit(boss, event, when):
        if boss.target_kinds.get(event.target) != 'interrupt':
            return native_hit(boss, event, when)
        if classify_hit(event.hit_tag) != HitFamily.WEAPON:
            raise ValueError('Private interrupt bridge requires a physical weapon packet')
        if len(receipts) + len(pending) >= capacity:
            raise ValueError('Private interrupt receipt capacity exceeded')
        key = id(event)
        if key in pending:
            raise ValueError('Private interrupt event is already awaiting publication')
        if id(boss) not in registries:
            registries[id(boss)] = (boss, InterruptRegistry(boss))
        registry = registries[id(boss)][1]
        before = registry.view(event.target)
        accounted = boss.interrupt_dealt.get(event.caster, 0.)
        result = native_hit(boss, event, when)
        if result != 'interrupt':
            raise ValueError('Native interrupt landing changed its kind')
        pending[key] = (event, boss, InterruptReceipt(
            event.caster, before.handle, event.target, when, event.damage,
            before, registry.view(event.target), accounted,
            boss.interrupt_dealt.get(event.caster, 0.)))
        return result

    def landing(manager, event, when, boss):
        if boss is None or boss.target_kinds.get(event.target) != 'interrupt':
            return native_landing(manager, event, when, boss)
        row = pending.pop(id(event), None)
        if row is None or row[0] is not event or row[1] is not boss or row[2].time != when:
            raise ValueError('Private interrupt publication requires its native landing receipt')
        receipts.append(row[2])

    _active = True
    try:
        with patch.object(BossScript, 'hit_target', hit), patch.object(BuffManager, 'publish_landing', landing):
            yield receipts
            if pending:
                raise ValueError('Unpublished private interrupt landing receipts')
    finally:
        _active = False
