"""Compact payload closure and fail-closed membership checks, with no GPU calls."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from portable_package_projection import project, validate, roots_for, check_command, SUPPORTED_SUITES


class ProjectionTests(unittest.TestCase):
    def test_current_shared_group_entries_are_explicitly_supported(self):
        self.assertTrue({'attack-group-battle','attack-group-native-route','attack-group-long'} <= set(SUPPORTED_SUITES))
    def fixture(self, root):
        sources = {
            'app/controller.py': 'import selected\n',
            'scripts/nikke_gpu.py': 'ALL = ["unrelated"]\n',
            'research/adapter.py': 'import importlib\nimportlib.import_module("dynamic")\n',
            'research/selected.py': 'from research import nested\n',
            'research/nested.py': 'PATH = "verify-leaf.py"\n',
            'research/dynamic.py': 'pass\n',
            'research/verify-leaf.py': 'pass\n',
            'research/unrelated.py': 'pass\n',
            'tests/test_selected.py': 'import selected\n',
            'tests/test_other.py': 'pass\n',
            'research/upstream/ref.py': 'pass\n',
            'gpu/unused.slang': '// retained even if not this entry\n',
            'tests/fixtures/unused.json': '{}',
        }
        for name, text in sources.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding='utf-8')
        return sources

    def test_transitive_static_dynamic_file_dependencies_and_all_nonpython_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);sources = self.fixture(root)
            selected, report = project(root, sources, ['research/adapter.py', 'tests/test_selected.py'])
            self.assertEqual(set(report['omitted']), {'research/unrelated.py', 'tests/test_other.py'})
            self.assertEqual(set(selected), set(sources) - set(report['omitted']))
            self.assertFalse(report['calculation_verified']);self.assertEqual(report['gpu_calls'], 0)
            for name in selected:
                self.assertEqual((root / name).read_text(), sources[name])

    def test_ambiguous_dynamic_filename_keeps_both_matches(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory);sources = self.fixture(root)
            for name in ('research/sub/dynamic.py', 'tests/dynamic.py'):
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('pass\n');sources[name]='pass\n'
            selected,_=project(root,sources,['research/adapter.py'])
            self.assertTrue({'research/dynamic.py','research/sub/dynamic.py','tests/dynamic.py'} <= set(selected))

    def test_missing_explicit_test_or_adapter_is_an_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sources=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'root absent'):
                project(root,sources,['tests/missing.py'])

    def test_controller_fixture_retains_tests_from_its_explicit_registry_suite(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sources=self.fixture(root)
            sources['tests/test_selected.py']='config=cli.SUITES["compiler-full"]\n'
            (root/'tests/test_selected.py').write_text(sources['tests/test_selected.py'])
            selected,_=project(root,sources,['tests/test_selected.py'],suite_tests={'compiler-full':['test_other.py']})
            self.assertIn('tests/test_other.py',selected)
            with self.assertRaisesRegex(ValueError,'suite test absent'):
                project(root,sources,['tests/test_selected.py'],suite_tests={'compiler-full':['missing.py']})

    def test_manifest_omission_cannot_remove_suite_smoke_gpu_or_pinned_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sources=self.fixture(root)
            config={'script':'research/adapter.py','tests':['test_selected.py']}
            roots=roots_for(config,[])
            for name in set(roots)-sources.keys():
                (root/name).write_text('pass\n');sources[name]='pass\n'
            selected,report=project(root,sources,roots)
            files=[{'path':name} for name in selected]
            validate(report,files,'destructible-skill-retention',config,[])
            for target in ('tests/test_selected.py','gpu/unused.slang','research/upstream/ref.py'):
                bad=copy.deepcopy(report);bad['omitted'].append(target);bad['omitted_files']+=1;bad['retained_files']-=1
                with self.assertRaisesRegex(ValueError,'compact|inventory'):
                    validate(bad,[r for r in files if r['path']!=target],'destructible-skill-retention',config,[])
            with self.assertRaisesRegex(ValueError,'projection'):
                validate(report,files,'destructible-skill-retention',config,['test_other.py'])

    def test_full_profile_unchanged_and_source_wide_commands_rejected_in_compact(self):
        check_command(None,'inventory')
        for command in ('run','_tests','_child','generation','audit','replay','seal','status','export'):
            check_command({'profile':'selected-suite-python-v1'},command)
        for command in ('inventory','reference','package','cases','audit-legacy'):
            with self.assertRaisesRegex(ValueError,'full checkout'):
                check_command({'profile':'selected-suite-python-v1'},command)


if __name__ == '__main__':
    unittest.main()
