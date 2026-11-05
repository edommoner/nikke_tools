"""Expected-mode activation probability; no CPU-produced activation decisions."""
import math
import re

KIND = 26
PREFIX = 'prob:'


def definitions(effects):
    return [i for i, (effect, _) in enumerate(effects)
            if any(c.startswith(PREFIX) for c in effect.get('trigger', {}).get('condition', []))]


def validate(effect):
    for condition in effect.get('trigger', {}).get('condition', []):
        if not isinstance(condition, str) or not condition.startswith(PREFIX):
            continue
        raw = condition[len(PREFIX):]
        if raw == '{0}':
            values = effect.get('trigger_values', {})
            if not isinstance(values, dict):
                raise ValueError('Probability trigger_values must be a mapping')
            candidates = list(values.values())
        else:
            if not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?', raw):
                raise ValueError('Invalid probability percentage')
            candidates = [raw]
        for value in candidates:
            if isinstance(value, bool):
                raise ValueError('Probability percentage must be numeric')
            try:
                number = float(value)
            except (TypeError, ValueError):
                raise ValueError('Invalid probability percentage') from None
            if not math.isfinite(number) or not 0 <= number <= 100:
                raise ValueError('Probability percentage must be finite and within0..100')
