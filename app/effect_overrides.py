"""Checked data corrections; calculation handlers never branch on character names."""
import copy
import hashlib
import json
from pathlib import Path

OVERRIDES = Path(__file__).resolve().parents[1] / 'data/engine-effect-overrides.json'


def apply_overrides(table, entries):
    result = copy.deepcopy(table)
    used = set()
    for entry in entries:
        name, match, changes = entry['character'], entry['match'], entry.get('set',{})
        delete=entry.get('delete',False);before=entry.get('move_before')
        if set(entry)-{'character','match','set','delete','move_before','evidence'} or type(delete) is not bool or delete and (changes or before is not None):raise ValueError('Invalid effect-data operation')
        if not isinstance(name, str) or not isinstance(match, dict) or not match.get('name') or not isinstance(changes, dict) or not (changes or delete or before):
            raise ValueError('Invalid effect-data correction')
        effects = result.get(name)
        if not isinstance(effects, list):
            raise ValueError('Effect-data correction character is missing: ' + name)
        indices = [i for i, effect in enumerate(effects) if all(effect.get(k) == v for k, v in match.items())]
        if len(indices) != 1:
            raise ValueError('Effect-data correction must match exactly one definition: ' + name + '/' + match['name'])
        selected=effects[indices[0]];key = (name, id(selected))
        if key in used:
            raise ValueError('Overlapping effect-data corrections')
        used.add(key)
        anchor=None
        if before is not None:
            if not isinstance(before,dict) or not before.get('name'):raise ValueError('Invalid effect-data ordering anchor')
            anchors=[effect for effect in effects if all(effect.get(k)==v for k,v in before.items())]
            if len(anchors)!=1 or anchors[0] is selected:raise ValueError('Effect-data ordering anchor must select one other definition')
            anchor=anchors[0]
        if delete:effects.pop(indices[0]);continue
        selected.update(copy.deepcopy(changes))
        if anchor is not None:
            effects.pop(indices[0]);effects.insert(next(i for i,effect in enumerate(effects) if effect is anchor),selected)
    return result


def install():
    from calculator import buff_manager
    data = OVERRIDES.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    previous = getattr(buff_manager, '_nikke_effect_overrides_digest', None)
    if previous is not None:
        if previous != digest:
            raise RuntimeError('Effect-data corrections changed; restart the worker')
        return
    entries = json.loads(data)['corrections']
    buff_manager._PARSED_SKILLS = apply_overrides(buff_manager._PARSED_SKILLS, entries)
    buff_manager._nikke_effect_overrides_digest = digest
