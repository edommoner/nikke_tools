"""Real-source cache identities; mutations are confined to temporary copies."""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
import parity_gate as gate


class IdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name)
        for folder in ('data', str(gate.ENGINE / 'data')):
            shutil.copytree(gate.ROOT / folder, cls.root / folder)
        for source in gate.cpu_sources():
            target = cls.root / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(gate.ROOT / source, target)
        cls.body = gate.load_corpus(gate.ROOT / 'research/parity/corpus.json')['squads'][0]['body'] if (gate.ROOT / 'research/parity/corpus.json').exists() else {'squad': ['에밀리아', '크라운', '앨리스', '루주', '헬름']}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def mutate(self, relative, change, assertion):
        path = self.root / relative
        original = path.read_bytes()
        try:
            value = gate.read(path)
            change(value)
            gate.atomic_json(path, value)
            assertion()
        finally:
            path.write_bytes(original)

    def test_unrelated_character_does_not_invalidate(self):
        before = gate.DataIdentity(self.root)
        member = before.member_identity(self.body['squad'])
        def verify():
            after = gate.DataIdentity(self.root)
            self.assertEqual(member, after.member_identity(self.body['squad']))
            self.assertEqual(before.global_identity, after.global_identity)
        for filename in ('parsed_nikke.json', 'parsed_skills.json', 'char_defaults.json'):
            self.mutate(gate.ENGINE / 'data' / filename,
                        lambda d: d.update({'unrelated-new-character': copy.deepcopy(d[self.body['squad'][0]])}) if filename != 'char_defaults.json' else d.update({'unrelated-new-character': {}}), verify)

    def test_member_skill_invalidates(self):
        before = gate.DataIdentity(self.root).member_identity(self.body['squad'])
        name = self.body['squad'][0]
        self.mutate(gate.ENGINE / 'data/parsed_skills.json',
                    lambda d: d[name].append({'name': 'changed skill entry', 'stat': 'atk_pct'}),
                    lambda: self.assertNotEqual(before, gate.DataIdentity(self.root).member_identity(self.body['squad'])))

    def test_code_change_invalidates(self):
        before, _ = gate.code_identity(self.root)
        path = self.root / gate.ENGINE / 'calculator/damage.py'
        original = path.read_bytes()
        try:
            path.write_bytes(original + b'\n# cache identity mutation\n')
            self.assertNotEqual(before, gate.code_identity(self.root)[0])
        finally:
            path.write_bytes(original)

    def test_global_data_invalidates(self):
        before = gate.DataIdentity(self.root).global_identity
        self.mutate(gate.ENGINE / 'data/tactics.json', lambda d: d.update({'changed-global': {}}),
                    lambda: self.assertNotEqual(before, gate.DataIdentity(self.root).global_identity))

    def test_skill_addition_for_other_character_is_stable(self):
        before = gate.DataIdentity(self.root).identities(self.body, 'code')
        self.mutate(gate.ENGINE / 'data/parsed_skills.json', lambda d: d.update({'new': [{'stat': 'atk_pct', 'value': 123}]}),
                    lambda: self.assertEqual(before, gate.DataIdentity(self.root).identities(self.body, 'code')))

    def test_dynamic_layers_and_optional_cpu_models_in_closure(self):
        sources = gate.cpu_sources(self.root)
        self.assertIn('app/target_context_runtime.py', sources)
        self.assertIn('app/product_reference_models.py', sources)
        self.assertIn(str(gate.ENGINE / 'runner/spec.py'), sources)
        self.assertNotIn('app/detail_gpu.py', sources)

    def test_cache_integrity_and_compression(self):
        with tempfile.TemporaryDirectory() as tmp:
            identity = gate.DataIdentity(self.root).identities(self.body, 'code')
            payload = {'total_damage': 123, 'large': ['same string'] * 1000}
            size = gate.save_cache(tmp, identity, payload)
            self.assertLess(size, len(gate.canonical(payload)))
            self.assertEqual(gate.load_cache(tmp, identity), payload)
            changed = dict(identity, request_sha256='different')
            with self.assertRaisesRegex(ValueError, 'Corrupt'):
                gate.load_cache(tmp, changed)

    def test_request_uses_product_canonical_json(self):
        import hashlib
        body = {'squad': ['에밀리아'], 'duration': 180.0}
        expected = hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
        self.assertEqual(gate.digest(body), expected)


class CorpusTests(unittest.TestCase):
    def test_compact_roundtrip_and_integrity(self):
        rows = [dict(id=1, members=['a'], body=dict(squad=['a'], profile={'x': [1, 2]}, duration=180.0)),
                dict(id=2, members=['b'], body=dict(squad=['b'], profile={'x': [1, 2]}, duration=30.0, extra=None))]
        with tempfile.TemporaryDirectory() as tmp:
            for suffix in ('.json', '.json.gz'):
                path = Path(tmp) / ('corpus' + suffix)
                gate.save_corpus(path, rows)
                restored = gate.load_corpus(path)['squads']
                self.assertEqual([gate.digest(r['body']) for r in rows], [gate.digest(r['body']) for r in restored])
            path = Path(tmp) / 'bad.json'
            gate.save_corpus(path, rows)
            value = gate.read(path)
            value['base']['duration'] = 10
            gate.atomic_json(path, value)
            with self.assertRaisesRegex(ValueError, 'reconstruction hash'):
                gate.load_corpus(path)

    def test_all_owner_pairs_have_burst_valid_witnesses(self):
        import parity_corpus as corpus
        source = gate.read(gate.ROOT / 'research/team-search/s1-inputs.json')
        chars = {c['name']: c for c in source['characters']['characters']}
        import itertools
        for pair in itertools.combinations_with_replacement(chars, 2):
            members = corpus.complete(pair, chars)
            self.assertEqual(len(set(members)), 5)
            self.assertTrue(corpus.covered(members, chars))
            self.assertTrue(set(pair) <= set(members))

    def test_pair_multiplicity_and_same_mechanism_pairs(self):
        import parity_corpus as corpus
        features = dict(a=['hp', 'hp'], b=['random'], c=['gauge'])
        candidates = [dict(id=i, members=m) for i, m in enumerate((['a','b'], ['b','a'], ['a','c'], ['c','a'], ['b','c'], ['c','b']))]
        universe = corpus.pair_set(['hp', 'hp', 'random', 'gauge'])
        selected, coverage = corpus.greedy(candidates, features, universe, 2)
        self.assertIn(('hp','hp'), universe)
        self.assertEqual(coverage['covered_pairs'], len(universe))
        self.assertEqual(coverage['minimum_observed'], 2)
        self.assertEqual(len(selected), 6)

    def test_definition_addresses_match_wire_schema(self):
        import parity_corpus as corpus
        from portable_specs import LIMITS as L, FIELDS as F
        inventory = {r['name']: r for r in corpus.reader_inventory()}
        self.assertEqual(inventory['stat']['address'], L['DEFINITION_BASE'] + F['STAT'])
        self.assertEqual(inventory['damageGauge']['stride'], L['DAMAGE_DEFINITION_WORDS'])
        self.assertEqual(inventory['healthScaling']['stride'], L['HEALTH_DEFINITION_WORDS'])

class CoverageTests(unittest.TestCase):
    OLD = 'K = 1\ndef covered(x=1):\n    return x + 1\ndef other():\n    return 2\nclass C:\n    a = 1\n    def method(self):\n        return 3\n'

    def check(self, new, valid, lines=(3,)):
        analysis = gate.source_changes({'a.py': self.OLD}, {'a.py': new})
        self.assertEqual(gate.coverage_valid(analysis, {'a.py': lines})[0], valid)
        return analysis

    def test_covered_and_uncovered_body(self):
        self.check(self.OLD.replace('x + 1', 'x + 2'), False)
        self.check(self.OLD.replace('return 2', 'return 9'), True)
        self.check(self.OLD.replace('return 3', 'return 9'), False, (9,))

    def test_comment_and_line_shifts(self):
        self.check('# comment\n\n' + self.OLD.replace('return x + 1', 'return x + 1 # comment'), True)
        self.check(self.OLD.replace('return 2', 'return 9') + '\n', True)

    def test_skeleton_changes(self):
        for new in (self.OLD + '\ndef added():\n    pass\n',
                    self.OLD.replace('x=1', 'x=2'), self.OLD.replace('a = 1', 'a = 2'),
                    self.OLD.replace('K = 1', 'K = 2')):
            self.assertTrue(self.check(new, False, ())['all_invalid'])
        self.assertTrue(gate.source_changes({'a': self.OLD}, {'a': self.OLD, 'b': ''})['all_invalid'])
        self.assertTrue(gate.source_changes({'a': self.OLD}, {})['all_invalid'])

    def test_nested_and_docstring(self):
        old = 'def outer():\n    def inner():\n        return 1\n    return inner()\n'
        analysis = gate.source_changes({'a': old}, {'a': old.replace('return 1', 'return 2')})
        self.assertEqual(analysis['changed'][0]['function'], 'outer')
        self.assertFalse(gate.coverage_valid(analysis, {'a': [4]})[0])
        old = 'def f():\n    "old"\n    pass\n'
        self.assertFalse(gate.coverage_valid(gate.source_changes({'a': old}, {'a': old.replace('old', 'new')}), {'a': [2]})[0])

    def test_comment_only_with_duplicate_qualified_names(self):
        old = 'class C:\n    def f(self):\n        return 1\n    def f(self):\n        return 2\n'
        analysis = gate.source_changes({'a': old}, {'a': '# comment\n' + old})
        self.assertTrue(gate.coverage_valid(analysis, {'a': [3, 5]})[0])

    def test_record_import_and_already_imported(self):
        import importlib.util
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); path = root / 'import_only.py'
            path.write_text('def f():\n    answer = 42\n    return answer\nf()\n')
            with gate.LineRecorder({'import_only.py': 'sha'}, root) as recorder:
                spec = importlib.util.spec_from_file_location('s8_import_only', path)
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
            try:
                self.assertIn(2, recorder.lines['import_only.py'])
                with self.assertRaisesRegex(RuntimeError, 'already imported'):
                    with gate.LineRecorder({'import_only.py': 'sha'}, root):
                        pass
            finally:
                del sys.modules[spec.name]

    def test_alias_chain_and_spot_check_failure(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp)
            old = dict(cache_key='a'*64, request_sha256='r', data_identity='d', code_identity=gate.digest({'a.py': 'sha'}))
            alias = dict(old, cache_key='b'*64, code_identity='b')
            current = dict(old, cache_key='c'*64, code_identity='c')
            gate.save_cache(cache, old, {'result': 1})
            gate.save_cache(cache, alias, {'result': 1}, reused_from=old['cache_key'])
            original = gate.original_entry(cache, gate.read(gate.cache_path(cache, alias['cache_key'])))
            self.assertEqual(original['identity'], old)
            with patch.object(gate, 'coverage_candidate', return_value=(original, [])), patch.object(gate, 'cpu_job', return_value={'result': 2}):
                payload, result = gate.reference_payload({}, current, cache, {}, spot_fraction=1)
            self.assertTrue(result['spot_checked'])
            self.assertTrue(result['spot_check_failure'])
            self.assertFalse(gate.cache_path(cache, current['cache_key']).exists())
            with patch.object(gate, 'coverage_candidate', return_value=(original, [])):
                payload, result = gate.reference_payload({}, current, cache, {}, spot_fraction=0)
            self.assertEqual(gate.read(gate.cache_path(cache, current['cache_key']))['reused_from'], old['cache_key'])
            self.assertEqual(result['reference_status'], 'coverage-reused')

    def test_spot_check_mismatch_exit_nonzero(self):
        summary = dict(spot_check_failures=1, regressions=[], counts={'unsupported': 0, 'cpu-fallback': 0})
        self.assertEqual(gate.run_failed(summary), 1)
        summary['spot_check_failures'] = 0
        self.assertEqual(gate.run_failed(summary), 0)

    def test_covered_change_cannot_inherit(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            old = dict(cache_key='a'*64, request_sha256='r', data_identity='d', code_identity='old')
            new = dict(old, cache_key='b'*64, code_identity='new')
            gate.save_cache(tmp, old, {'value': 1})
            reason = dict(file='a.py', function='covered', first=2, last=4)
            with patch.object(gate, 'coverage_candidate', return_value=(None, [reason])), patch.object(gate, 'cpu_job', return_value={'value': 2}):
                payload, result = gate.reference_payload({}, new, tmp, {}, inherited_identity=old)
            self.assertEqual(payload, {'value': 2})
            self.assertEqual(result['cpu_evaluations'], 1)
            self.assertEqual(result['reference_status'], 'current-reference')
            self.assertFalse(result['previous_code_payload_equal'])
            self.assertEqual(result['invalidating'], [reason])

    def test_original_source_reuse_after_line_shifts(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'tree'; root.mkdir()
            cache = Path(tmp) / 'cache'
            path = root / 'a.py'; path.write_text(self.OLD)
            sources = {'a.py': hashlib.sha256(path.read_bytes()).hexdigest()}
            old = dict(cache_key='a'*64, request_sha256='r', data_identity='d', code_identity=gate.digest(sources))
            gate.store_sources(cache, sources, root)
            gate.save_cache(cache, old, {'v': 1})
            gate.atomic_gzip(gate.coverage_path(cache, old['cache_key']), gate.canonical(dict(cache_key=old['cache_key'], code_identity=sources, lines={'a.py': [3]})))
            # Alias generation shifts lines; later reuse must still see original line 3.
            alias = dict(old, cache_key='b'*64, code_identity='intermediate')
            gate.save_cache(cache, alias, {'v': 1}, reused_from=old['cache_key'])
            path.write_text('# shifted\n' + self.OLD.replace('return 2', 'return 8'))
            current = {'a.py': hashlib.sha256(path.read_bytes()).hexdigest()}
            gate.store_sources(cache, current, root)
            entry = gate.original_entry(cache, gate.read(gate.cache_path(cache, alias['cache_key'])))
            self.assertEqual(gate.coverage_candidate(cache, [entry], current)[0]['identity'], old)
            path.write_text('# shifted\n' + self.OLD.replace('x + 1', 'x + 8'))
            current = {'a.py': hashlib.sha256(path.read_bytes()).hexdigest()}
            gate.store_sources(cache, current, root)
            candidate, reasons = gate.coverage_candidate(cache, [entry], current)
            self.assertIsNone(candidate)
            self.assertEqual(reasons[0]['function'], 'covered')


if __name__ == '__main__':
    unittest.main()
