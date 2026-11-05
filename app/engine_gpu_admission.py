"""Fail closed for unconnected reference-engine keys in the shared compiler."""


class UnsupportedEngineKeys(ValueError):
    pass


# Empty shared refusal sets remain extensible and testable.
SHARED_TARGETS = frozenset()
SHARED_STATS = frozenset()
SHARED_CONDITIONS = frozenset()

def require_supported(effects, cubes=()):
    keys = set()
    def rows(value):
        if isinstance(value, dict):
            yield value
            for child in value.values():
                yield from rows(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                yield from rows(child)

    for effect in rows(list(effects)):
        for field, values in (
            ('target', SHARED_TARGETS),
            ('stat', SHARED_STATS),
        ):
            value = effect.get(field)
            if isinstance(value, str) and value in values:
                keys.add(field + ':' + value)
        conditions = effect.get('condition', [])
        if isinstance(conditions, str):
            conditions = [conditions]
        for condition in conditions:
            if condition in SHARED_CONDITIONS:
                keys.add('condition:' + condition)
    if keys:
        raise UnsupportedEngineKeys('Unsupported shared reference engine keys: ' + ', '.join(sorted(keys)))
