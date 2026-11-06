"""Settings-scoped, compiled-wire mechanism pair coverage (no CPU battles)."""
from __future__ import annotations

import collections
import copy
import itertools
import random
import re
import struct
from pathlib import Path

import parity_gate as gate


def covered(members, chars):
    stages = [chars[n]['burst'] for n in members]
    return sum(s not in stages for s in ('1', '2', '3')) <= stages.count('A')


def complete(required, chars, rng=None):
    """A constructive feasibility witness: at most two owners + three stages."""
    members = list(dict.fromkeys(required))
    names = list(chars)
    if rng is not None:
        rng.shuffle(names)
    for stage in ('1', '2', '3'):
        if not covered(members, chars):
            stages = [chars[n]['burst'] for n in members]
            if stage not in stages:
                name = next((n for n in names if n not in members and chars[n]['burst'] == stage), None)
                if name is not None:
                    members.append(name)
    for name in names:
        if len(members) >= 5:
            break
        if name not in members:
            members.append(name)
    if len(members) != 5 or not covered(members, chars):
        raise ValueError('Cannot construct valid squad for ' + str(required))
    return members


def reader_inventory():
    """Read addresses from the actual shared Definition accessors, fail closed.

    Only literal arithmetic over schema constants is accepted. No authored
    effect names, character identities or raw magnitudes become mechanisms.
    """
    from portable_specs import LIMITS, FIELDS
    source = (gate.ROOT / 'gpu/definition_runtime.slang').read_text()
    env = {'input': 0, 'row': 0, **{'P_' + k: v for k, v in LIMITS.items()},
           **{'D_' + k: v for k, v in FIELDS.items()}}
    readers = []
    for typ, name, body in re.findall(r'(uint64_t|uint|int) definition_(\w+)\(uint input,uint row\)\s*\{([^}]+)\}', source):
        match = re.search(r'(?:commands\[|loadNumber\()(.+?)(?:\]|\);)', body)
        if not match:
            raise ValueError('Unrecognized Definition reader: ' + name)
        expr = match[1]
        if not re.fullmatch(r'[\w\s()+*]+', expr):
            raise ValueError('Unrecognized Definition address: ' + expr)
        # All names must be known schema constants. AST evaluation has no calls,
        # attributes, indexing or builtins; expression is repository-owned.
        address = eval(expr, {'__builtins__': {}}, env)
        env['row'] = 1
        stride = eval(expr, {'__builtins__': {}}, env) - address
        env['row'] = 0
        readers.append(dict(name=name, type=typ, address=address, stride=stride, expression=expr))
    if not readers:
        raise ValueError('No compiled Definition readers found')
    return readers


IDENTITIES = {'owner', 'name', 'eventName', 'targetName', 'alias', 'statKey', 'group',
              'durationGroup', 'periodicGroup', 'lazyGroup', 'recipients'}
ENUMS = {'kind', 'stat', 'event', 'countMode', 'target', 'stageArg', 'stageOverride',
         'damageRoute', 'healthScaling', 'enemyBuff', 'polarity', 'buffEvent'}


def bucket(value):
    return 'negative' if value < 0 else 'zero' if value == 0 else 'one' if value == 1 else 'many'


def wire_features(words, index, readers):
    features = set()
    for reader in readers:
        name = reader['name']
        if name == 'owner':
            continue
        at = reader['address'] + index * reader['stride']
        value = words[at]
        if name == 'lazyGroup':
            value >>= 4
        if reader['type'] == 'uint64_t':
            value = struct.unpack('<d', struct.pack('<II', *words[at:at+2]))[0]
            features.add(name + ':' + bucket(value))
        elif name in IDENTITIES:
            # Names/group IDs are local allocation artifacts. Presence is useful;
            # the actual identity would collapse mechanism coverage into roster coverage.
            if name in ('eventName', 'targetName', 'alias'):
                value = value != 0xffffffff
            else:
                value = bool(value)
            features.add(name + ':present=' + str(int(value)))
        elif name in ENUMS:
            features.add(name + ':' + str(value))
        elif 'flags' in name.lower() or name in ('mergeEligible', 'queryResolve'):
            if name == 'mergeEligible':
                value &= 3
            if name == 'queryResolve':
                value = (value >> 2) & 1
            features.update(name + ':bit=' + str(bit) for bit in range(32) if value & (1 << bit))
        else:
            if reader['type'] == 'int' and value >= 2**31:
                value -= 2**32
            features.add(name + ':' + bucket(value))
    from portable_specs import LIMITS as L, FIELDS as F
    definition = L['DEFINITION_BASE'] + index * L['DEFINITION_WORDS']
    for slot in range(words[definition + F['TRIGGER_COUNT']]):
        at = L['EVENT_BASE'] + index * L['EVENT_WORDS'] + slot * 8
        features.add('trigger:event=' + str(words[at]))
        features.add('trigger:count-mode=' + str(words[at+3]))
        stage = words[at+7]
        if stage >= 2**31:
            stage -= 2**32
        features.add('trigger:stage=' + str(stage))
    for slot in range(words[definition + F['CONDITION_COUNT']]):
        at = L['CONDITION_BASE'] + index * L['CONDITION_WORDS'] + slot * 4
        features.add('condition:type=' + str(words[at]))
    at = L['RECIPIENT_BASE'] + index * 8
    nodes = [at]
    if words[at] == 17:
        nodes += [L['RECIPIENT_NODE_BASE'] + (words[at+2]+n)*8 for n in range(words[at+1])]
    for at in nodes:
        features.add('recipient:kind=' + str(words[at]))
        features.add('recipient:count=' + bucket(words[at+1]))
    at = L['RESOURCE_DEFINITION_BASE'] + index * 10
    features.add('resource:operation=' + str(words[at]))
    features.update('resource:flag=' + str(bit) for bit in range(32) if words[at+2] & (1 << bit))
    at = L['MODE_BASE'] + index * L['MODE_WORDS']
    if any(words[at:at+L['MODE_WORDS']]):
        features.add('weapon:mode-change')
    return features


def extract(base, rows, chars):
    import portable_detail
    source_paths = sorted((gate.ROOT / 'app').glob('*.py')) + sorted((gate.ROOT / 'gpu').glob('*.slang'))
    identity = gate.digest(dict(base=base, chars=chars,
                               sources={p.relative_to(gate.ROOT).as_posix(): __import__('hashlib').sha256(p.read_bytes()).hexdigest() for p in source_paths},
                               data=gate.DataIdentity().identities(dict(base, squad=list(chars)), gate.code_identity()[0])))
    cache = gate.ROOT / 'research/parity/features' / (identity + '.json')
    if cache.exists():
        saved = gate.read(cache)
        return saved['features'], saved['inventory']
    readers = reader_inventory()
    remaining = set(chars)
    result = {}
    contexts = []
    candidates = [r for r in rows if covered(r['members'], chars)]
    # One complete real context per character, chosen deterministically from S1.
    # Shared settings and growth are identical to the requests that will be run.
    while remaining:
        row = max(candidates, key=lambda r: len(remaining.intersection(r['members'])))
        if not remaining.intersection(row['members']):
            row = dict(members=complete([min(remaining)], chars))
        prepared, _ = portable_detail.prepare(dict(base, squad=row['members']))
        source, _, _, words, metadata = portable_detail.compile_product(prepared)
        context = dict(members=row['members'], source=source)
        contexts.append(context)
        from portable_specs import LIMITS as L, FIELDS as F
        features = {n: collections.Counter() for n in row['members']}
        for index in range(words[1]):
            owner = words[L['DEFINITION_BASE'] + index * L['DEFINITION_WORDS'] + F['OWNER']]
            features[row['members'][owner]].update(wire_features(words, index, readers))
        for n in sorted(remaining.intersection(row['members'])):
            weapon = next(c['_weapon'] for c in prepared['chars'] if c['name'] == n)
            features[n].update(['weapon:type=' + str(weapon['weapon_type'])])
            result[n] = sorted(f for f, count in features[n].items() for _ in range(min(2, count)))
        remaining.difference_update(row['members'])
    inventory = dict(readers=readers, contexts=contexts)
    gate.atomic_json(cache, dict(features=result, inventory=inventory))
    return result, inventory


def pair_set(features):
    counts = collections.Counter(features)
    return set(itertools.combinations(sorted(counts), 2)) | {(f, f) for f, count in counts.items() if count > 1}


def squad_features(members, features):
    return itertools.chain.from_iterable(features[n] for n in members)


def pair_witness(required, chars, features, missing, rng):
    """Complete a two-owner witness with useful, valid extra mechanisms."""
    members = list(dict.fromkeys(required))
    names = sorted(chars)
    rng.shuffle(names)
    def choose(choices):
        def gain(n):
            present = collections.Counter(squad_features([*members, n], features))
            return sum(present[a] > 0 and present[b] > 0 and (a != b or present[a] > 1) for a, b in missing)
        return max(choices, key=gain)
    for stage in ('1', '2', '3'):
        if not covered(members, chars) and stage not in [chars[n]['burst'] for n in members]:
            members.append(choose([n for n in names if n not in members and chars[n]['burst'] == stage]))
    while len(members) < 5:
        members.append(choose([n for n in names if n not in members]))
    if len(members) != 5 or not covered(members, chars):
        raise ValueError('Invalid mechanism witness')
    return members


def greedy(candidates, features, universe, multiplicity=1, initial=()):
    """Exact greedy marginal gain on a finite pool; witnessed closure of universe."""
    labels = sorted(universe)
    lookup = {p: i for i, p in enumerate(labels)}
    mask_cache = {}
    def mask(members):
        key = tuple(sorted(members))
        if key not in mask_cache:
            indices = sorted(lookup[p] for p in pair_set(squad_features(members, features)) if p in lookup)
            raw = bytearray((len(labels)+7)//8)
            for i in indices:
                raw[i//8] |= 1 << (i%8)
            mask_cache[key] = int.from_bytes(raw, 'little')
        return mask_cache[key]
    counts = [0] * len(labels)
    def credit(bits):
        while bits:
            bit = bits & -bits
            counts[bit.bit_length()-1] += 1
            bits ^= bit
    selected = list(initial)
    seen = {tuple(r['members']) for r in initial}
    for row in initial:
        credit(mask(row['members']))
    pool = [(row, mask(row['members'])) for row in candidates if tuple(row['members']) not in seen]
    while True:
        needed = sum(1 << i for i, count in enumerate(counts) if count < multiplicity)
        if not needed:
            break
        best = max(range(len(pool)), key=lambda i: (pool[i][1] & needed).bit_count(), default=None)
        if best is None or not (pool[best][1] & needed):
            raise ValueError('Candidate pool does not witness all required pairs')
        row, bits = pool.pop(best)
        selected.append(row)
        credit(bits)
    return selected, dict(pair_count=len(labels), covered_pairs=sum(c >= multiplicity for c in counts),
                          multiplicity=multiplicity, minimum_observed=min(counts, default=0))


def build(args):
    source = gate.read(gate.ROOT / 'research/team-search/s1-inputs.json')
    base = gate.read(args.benchmark or source['benchmark'])[0]
    base.update(source['settings'])
    chars = {c['name']: c for c in source['characters']['characters']}
    rows = [__import__('json').loads(line) for line in (gate.ROOT / 'research/team-search/s1-results.jsonl').read_text().splitlines()]
    name = args.extend_for_character
    if name and name not in chars:
        import engine_worker
        if name not in engine_worker.META:
            raise ValueError('Unknown canonical character: ' + name)
        if name not in base['profile']['chars']:
            base['profile']['chars'][name] = {k: copy.deepcopy(v) for k, v in engine_worker.spec.DEFAULT_CHAR.items() if k in engine_worker.spec.GROWTH_KEYS}
        scored = engine_worker.candidate_scores(dict(evaluation=base))
        chars = {c['name']: c for c in scored['characters']}
    features, inventory = extract(base, rows, chars)
    setting_features = {'setting:' + k + '=' + str(base.get(k)) for k in ('burst_gauge_mode', 'burst_policy')}
    setting_features.add('enemy:code=' + str(base.get('enemy', {}).get('code')))
    for values in features.values():
        values.extend(sorted(setting_features))
    all_features = set().union(*(set(v) for v in features.values()))
    universe = pair_set(itertools.chain.from_iterable(features.values()))
    # Each feature belongs to an actual character. Any two owners fit with one
    # stage-1/2/3 member each, so all these pairs have constructive valid witnesses.
    providers = collections.defaultdict(list)
    # JSON cache publication sorts dictionary keys. Restore the compiler-context
    # order so cold and warm feature caches choose identical witnesses.
    provider_order = list(dict.fromkeys(n for context in inventory['contexts']
                                       for n in sorted(context['members'])))
    for n in provider_order:
        for f in features[n]:
            providers[f].append(n)
    candidates = [dict(r) for r in rows if covered(r['members'], chars)]
    rng = random.Random(args.seed)
    seen = {tuple(r['members']) for r in candidates}
    def add(members):
        if tuple(members) not in seen:
            seen.add(tuple(members))
            candidates.append(dict(id=None, members=members))
    for _ in range(1500):
        members = rng.sample(sorted(chars), 5)
        if covered(members, chars) and (not name or name in members):
            add(members)
    initial = []
    if name:
        if not args.corpus:
            raise ValueError('--extend-for-character requires --corpus')
        initial = gate.load_corpus(args.corpus)['squads']
        # Only pairs involving a feature the named character carries are targets.
        nf = set(features[name])
        universe = {p for p in universe if nf.intersection(p)}
        candidates = [r for r in candidates if name in r['members']]
        seen = {tuple(r['members']) for r in candidates}
    # Fill pool gaps with direct real witnesses; repeat with distinct ordered
    # squads for k>1. This certifies closure rather than assuming random coverage.
    counts = collections.Counter()
    for row in [*initial, *candidates]:
        counts.update(pair_set(squad_features(row['members'], features)))
    for a, b in sorted(universe):
        for _ in range(max(0, args.multiplicity-counts[a,b])):
            owners = [providers[a][0], providers[b][0]]
            if a == b and features[providers[a][0]].count(a) == 1:
                owners = list(dict.fromkeys(providers[a]))[:2]
            # A named owner + two feature owners may need >5 slots. Prefer its
            # feature as one provider, reducing this to at most two owners.
            if name:
                owners = [name, providers[b][0] if a in features[name] else providers[a][0]]
            missing = {p for p in universe if counts[p] < args.multiplicity}
            members = pair_witness(owners, chars, features, missing, rng)
            while tuple(members) in seen:
                rng.shuffle(members)
            add(members)
            counts.update(pair_set(squad_features(members, features)))
    selected, coverage = greedy(candidates, features, universe, args.multiplicity, initial)
    if name:
        added = len(selected)-len(initial)
        selected_members = {tuple(r['members']) for r in selected}
        for row in candidates:
            if added >= args.minimum_character_squads:
                break
            if tuple(row['members']) not in selected_members:
                selected.append(row)
                selected_members.add(tuple(row['members']))
                added += 1
    used = {r['id'] for r in selected if r['id'] is not None}
    next_id = max([r['id'] for r in rows] + list(used)) + 1
    initial_ids = {r['id'] for r in initial}
    for row in selected:
        if row['id'] is None:
            row['id'] = next_id
            next_id += 1
        if 'body' not in row:
            row['body'] = dict(base, squad=row['members'])
    if len({r['id'] for r in selected}) != len(selected) or len({gate.digest(r['body']) for r in selected}) != len(selected):
        raise ValueError('Covering corpus must contain unique IDs and requests')
    random_pairs = set()
    for row in rows:
        random_pairs.update(pair_set(squad_features(row['members'], features)))
    report = dict(coverage, squads=len(selected), features=len(all_features), settings_sha256=gate.digest(base),
                  random_s1=dict(squads=len(rows), covered_pairs=len(random_pairs & universe), pair_count=len(universe)),
                  extended_character=name, added_squads=len(selected)-len(initial) if name else None,
                  added_ids=[r['id'] for r in selected if r['id'] not in initial_ids] if name else None)
    gate.save_corpus(args.output, selected, seed=args.seed, coverage=report)
    gate.atomic_json(Path(str(args.output) + '.features.json'), dict(characters=features, inventory=inventory, report=report))
    print(__import__('json').dumps(report, ensure_ascii=False), flush=True)
