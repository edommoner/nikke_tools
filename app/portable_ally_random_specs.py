"""Literal friendly selector metadata, sharing revival's global MT stream."""
import re

MAGIC = 0x41524731
SELECTORS = (19, 25)


def contains(target):
    if isinstance(target, list):
        return any(contains(item) for item in target)
    return isinstance(target, str) and re.fullmatch(
        r'allies_random:[0-5]|allies_broken_cover_random:\d+', target) is not None


def validate(effect, *, combat, world_frame):
    target = effect.get('target', 'self')
    if not contains(target):
        return
    if combat is None or not world_frame:
        raise ValueError('Friendly random recipients require a private combat world')
    if effect.get('type') not in ('buff', 'instant'):
        raise ValueError('Friendly random recipients require buff or instant effects')
    if effect.get('type') == 'buff' and isinstance(target, list):
        raise ValueError('Ordered random buff lists require a separate lazy-list contract')


def pack(words, limits, effects, seed, snapshot_logging=False):
    if not any(contains(effect.get('target', 'self')) for effect, _ in effects):
        return
    if type(seed) is not int or not 0 <= seed <= 2**64-1:
        raise ValueError('Friendly random recipients require an unsigned64 allied RNG seed')
    at = limits['RECIPIENT_META_BASE'] + 2
    words[at:at+3] = [MAGIC, seed & 0xffffffff, seed >> 32]
    if any(effect.get('type')=='buff' and effect.get('stat') in ('atk_from_hp_pct','atk_caster_based_pct')
           and isinstance(effect.get('target'),str) and re.fullmatch(r'allies_random:[1-5]',effect['target'])
           for effect,_ in effects):
        words[limits['RECIPIENT_META_BASE']+5]=0x4e515231
        words[limits['RECIPIENT_META_BASE']+6]=int(snapshot_logging)
