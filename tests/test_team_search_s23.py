"""Exact conditional coverage and scorer workspace reuse contracts."""
import copy
import importlib.util
import itertools
from pathlib import Path
import struct
import sys
import unittest

HERE = Path(__file__).resolve().parents[1]/'research/team-search'
sys.path.insert(0, str(HERE))
import l2_fast
import l2_score
import l2_score_s20


def synthetic():
    spec = importlib.util.spec_from_file_location('s23_verify', HERE/'l2_fast/verify.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.synthetic()


class ExactSearchTests(unittest.TestCase):
    def test_conditional_stage_coverage(self):
        library = l2_fast.build()
        # Exercise other-B1 tests from both B1 and non-B1 sources, plus squad
        # membership and the general condition-code fallback.
        for source, condition in [('d', 1), ('d', 2), ('a', 1), ('a', 2), ('d', 3), ('d', -1)]:
            for mask in (0, 2, 15):
                with self.subTest(source=source, condition=condition, mask=mask):
                    p = synthetic()
                    p['s20'] = dict(version=2, switches=mask)
                    p['characters'][source]['mechanics_s20'] = [[1, 0, condition, 1, 1., 0, 0]]
                    fast = l2_fast.Score(p, library=library)
                    oracle = l2_score_s20.Score(p)
                    names = list(p['characters'])
                    expected = []
                    cycle = l2_score_s20.cycle if mask & 2 else l2_score.cycle
                    for ids in itertools.combinations(range(len(names)), 5):
                        squad = [names[i] for i in ids]
                        if cycle(squad, p['characters'], 180.)[2]:
                            expected.append((list(ids), oracle(squad)))
                    expected.sort(key=lambda row: (-row[1], row[0]))
                    result = l2_fast.enumerate_top(fast, list(range(len(names))), 100, 1)
                    self.assertEqual(result['counts']['visited'], 21)
                    self.assertEqual(result['counts']['scored'], len(expected))
                    self.assertEqual(len(result['entries']), len(expected))
                    for actual, (ids, score) in zip(result['entries'], expected):
                        self.assertEqual(actual['indices'], ids)
                        self.assertEqual(struct.pack('<d', actual['score']), struct.pack('<d', score))
                    fast.close()

    def test_alternating_table_widths_and_repeated_member_outputs(self):
        library = l2_fast.build()
        small = synthetic()
        wide = copy.deepcopy(small)
        for c in wide['characters'].values():
            c['groups'][0]['own'].update({f'unused_{i}': float(i) for i in range(257)})
        for p in (small, wide, small, wide, small):
            fast = l2_fast.Score(p, library=library)
            oracle = l2_score.Score(p)
            squads = [list(s) for s in itertools.islice(itertools.permutations(p['characters'], 5), 32)]
            for batch in (squads, list(reversed(squads)), squads[:1]):
                totals, members = fast.score_indices(fast._indices(batch), True)
                for i, squad in enumerate(batch):
                    values = oracle.member_scores(squad)
                    expected = struct.pack('<6d', max(sum(values.values()), 1.), *values.values())
                    actual = struct.pack('<6d', totals[i], *members[i*5:i*5+5])
                    self.assertEqual(actual, expected)
            fast.close()


if __name__ == '__main__':
    unittest.main()
