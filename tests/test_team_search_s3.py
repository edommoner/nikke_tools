"""Observe the real shared executor's existing numeric epoch and resource words."""
import array
import copy
import json
from collections import defaultdict
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
import portable_detail as product
from portable_product_ammo import compile_product as compile_ammo
from portable_backend import execute
from portable_specs import LIMITS as L


class ResourceNumericEpochTests(unittest.TestCase):
    def test_only_changed_charge_and_every_consume_variant_invalidate(self):
        fixture = json.loads((ROOT / 'tests/fixtures/team-search-s2-v1.json').read_text())
        squad = next(c['squad'] for c in fixture['cases'] if c['id'] == 366)
        prepared, _ = product.prepare(dict(fixture['base'], squad=squad, duration=1))
        # Keep an inactive late random reader to enable the production cache.
        reader = copy.deepcopy(next(r for r in prepared['effects']
                                    if r['effect'].get('stat') == 'atk_caster_based_pct'
                                    and r['effect'].get('target') == 'allies_random:1'))
        reader['effect']['trigger'] = dict(timing=['every:15s'], condition=[])
        owner = reader['owner']
        variants = [('charge-zero', 'gauge_charge', 0., 0., 0., 0),
                    ('charge', 'gauge_charge', 0., 1., 1., 1),
                    ('charge-capped', 'gauge_charge', 5., 1., 5., 0),
                    ('charge-rounded', 'gauge_charge', 1e16, 1., 1e16, 0)]
        for stat in ('gauge_consume', 'gauge_consume_as_ammo'):
            variants.extend([(stat + '-empty', stat, 0., 1., 0., 0),
                             (stat + '-zero', stat, 5., 0., 5., 0),
                             (stat + '-partial', stat, 5., 2., 3., 1),
                             (stat + '-all', stat, 5., -1., 0., 1),
                             (stat + '-all-empty', stat, 0., -1., 0., 0),
                             (stat + '-rounded', stat, 1e16, 1., 1e16, 0)])
        programs = []
        for label, stat, old, amount, expected_value, bump in variants:
            # Each pair has the same initial charge and differs only in the
            # tested mutation. No notification listeners or active buffs exist.
            for value in (0., amount):
                pr = copy.deepcopy(prepared)
                def resource(name, kind, quantity):
                    return dict(owner=owner, effect=dict(source='스킬1', type='instant',
                        name=name, stat=kind, target='self', fixed_value=quantity,
                        gauge_id='epoch-test', gauge_max=max(5., old),
                        trigger=dict(timing=['battle_start'], condition=[])))
                pr['effects'] = [copy.deepcopy(reader), resource('initial', 'gauge_charge', old),
                                 resource('mutation', stat, value)]
                programs.append(compile_ammo(pr, product.compile_product))
        groups = defaultdict(list)
        for index, (source, iw, ow, words, _) in enumerate(programs):
            groups[source, iw, ow].append((index, words))
        blocks = {}
        for (source, iw, ow), members in groups.items():
            packed = array.array('I', [len(members)])
            for _, words in members:
                packed.extend(words)
            if sys.byteorder != 'little': packed.byteswap()
            with tempfile.TemporaryDirectory(prefix='s3-resource-epoch-') as tmp:
                path = Path(tmp) / 'readback.bin'
                execute(source, 'portableEvents', packed.tobytes(), iw, ow, 'native', readback_path=path)
                raw = array.array('I'); raw.frombytes(path.read_bytes())
                if sys.byteorder != 'little': raw.byteswap()
            for offset, (index, _) in enumerate(members):
                # Retain just the observed header and gauge, not large tails.
                blocks[index] = raw[offset*ow:offset*ow+L['NATIVE_QUERY_BASE']+32]
        for index, (label, _, old, _, expected, bump) in enumerate(variants):
            with self.subTest(label=label):
                control = blocks[2*index]
                changed = blocks[2*index+1]
                self.assertEqual((control[0], changed[0]), (0, 0))
                h = L['NATIVE_QUERY_BASE']
                self.assertEqual(changed[h], 0x4e515231)
                self.assertEqual(changed[h+1] - control[h+1], bump)
                owner_index = next(i for i, c in enumerate(prepared['chars']) if c['name'] == owner)
                at = L['RESOURCE_STATE_BASE'] + owner_index * L['RESOURCE_KEYS'] * 5 + 1
                actual = struct.unpack('<d', struct.pack('<II', *changed[at:at+2]))[0]
                self.assertEqual(actual, expected)


if __name__ == '__main__':
    unittest.main()
