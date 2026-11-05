"""Offline upgrade/install tests use local ZIPs and explicit fake revision bytes."""
import ast,contextlib,copy,hashlib,importlib.util,io,json,shutil,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('portable_engine_setup',ROOT/'scripts/setup-engine.py')
setup=importlib.util.module_from_spec(spec);spec.loader.exec_module(setup)
pins=setup.pins
PRODUCTION=copy.deepcopy(pins.REVISIONS)

class EngineSetupTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # Import the real product before per-test fake identity manifests are installed.
  import engine_worker
  cls.worker=engine_worker
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve()
  self.names=(*setup.REQUIRED,'calculator/timeline.py','calculator/buff_manager.py','calculator/damage.py','data/parsed_skills.json','data/base_stat_tables/cube.json','LICENSE')
  self.contents={r:{n:(r+':'+n).encode() for n in (*self.names,'README.md')} for r in (setup.REVISION,setup.HISTORICAL_REVISION)}
  manifests={r:dict(files={n:hashlib.sha256(b).hexdigest() for n,b in files.items()},required=list(self.names)) for r,files in self.contents.items()}
  self.patch=patch.object(pins,'REVISIONS',manifests);self.patch.start();self.addCleanup(self.patch.stop)
  no_network=patch.object(setup.urllib.request,'urlopen',side_effect=AssertionError('Network forbidden in offline setup tests'));no_network.start();self.addCleanup(no_network.stop)
 def tree(self,revision,destination='nikke-calc-master'):
  tree=self.root/'research/upstream'/destination
  for name,data in self.contents[revision].items():
   path=tree/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
  return tree
 def archive(self,revision=None,*,prefix=None,comment=None,changes=None,extra=None,symlink=False,duplicate=False):
  revision=revision or setup.REVISION;prefix=prefix or 'nikke-calc-'+revision;path=self.root/(revision+'.zip')
  with zipfile.ZipFile(path,'w') as z:
   z.comment=(comment or revision).encode()
   for name,data in self.contents[revision].items():
    z.writestr(prefix+'/'+name,(changes or {}).get(name,data))
   if extra:
    entry=zipfile.ZipInfo(extra)
    if symlink:entry.external_attr=0o120777<<16
    z.writestr(entry,b'invalid')
   if duplicate:
    with self.assertWarns(UserWarning):z.writestr(prefix+'/'+setup.REQUIRED[0],self.contents[revision][setup.REQUIRED[0]])
  return path
 def snapshot(self,tree):return {str(p.relative_to(tree)):p.read_bytes() for p in tree.rglob('*') if p.is_file()}
 def test_fresh_offline_install_and_verified_idempotence(self):
  archive=self.archive();result=setup.setup(self.root,archive)
  self.assertFalse(result['already_present']);self.assertEqual(pins.identify(Path(result['engine'])),setup.REVISION)
  self.assertTrue(setup.setup(self.root)['already_present'])
 def test_master_archive_prefix_is_accepted(self):
  self.assertFalse(setup.setup(self.root,self.archive(prefix='nikke-calc-master'))['already_present'])
 def test_old_install_is_moved_intact_then_upgraded(self):
  old=self.tree(setup.HISTORICAL_REVISION)
  (old/'.DS_Store').write_bytes(b'Finder metadata')
  (old/'calculator/Thumbs.db').write_bytes(b'Explorer metadata')
  (old/'data/desktop.ini').write_bytes(b'Explorer metadata')
  (old/'calculator/._timeline.py').write_bytes(b'AppleDouble metadata')
  before=self.snapshot(old)
  result=setup.setup(self.root,self.archive());preserved=Path(result['preserved_engine'])
  self.assertEqual(preserved.name,'nikke-calc-23164e4');self.assertEqual(self.snapshot(preserved),before)
  self.assertEqual(pins.identify(old),setup.REVISION)
 def test_modified_old_tree_is_refused_without_any_move(self):
  old=self.tree(setup.HISTORICAL_REVISION);(old/'runner/sim.py').write_text('local change');before=self.snapshot(old)
  with self.assertRaisesRegex(ValueError,'Unknown or modified installed'):setup.setup(self.root,self.archive())
  self.assertEqual(self.snapshot(old),before);self.assertFalse((old.parent/'nikke-calc-23164e4').exists())
 def test_modified_current_tree_is_refused_instead_of_already_present(self):
  tree=self.tree(setup.REVISION);(tree/'README.md').write_text('modified support file')
  with self.assertRaisesRegex(ValueError,'Unknown or modified installed'):setup.setup(self.root,self.archive())
  self.assertEqual((tree/'README.md').read_text(),'modified support file')
 def test_unknown_extra_file_is_refused(self):
  tree=self.tree(setup.HISTORICAL_REVISION);(tree/'unknown.py').write_text('unknown')
  with self.assertRaisesRegex(ValueError,'Unknown or modified installed'):setup.setup(self.root,self.archive())
  self.assertTrue((tree/'unknown.py').exists())
 def test_missing_runtime_file_is_refused(self):
  tree=self.tree(setup.HISTORICAL_REVISION);(tree/'calculator/damage.py').unlink()
  with self.assertRaisesRegex(ValueError,'Unknown or modified installed'):setup.setup(self.root,self.archive())
 def test_bytecode_cache_does_not_change_revision_identity(self):
  tree=self.tree(setup.REVISION);cache=tree/'calculator/__pycache__';cache.mkdir();(cache/'damage.cpython-312.pyc').write_bytes(b'cache')
  self.assertTrue(setup.setup(self.root)['already_present'])
 def test_os_metadata_is_ignored_at_every_approved_depth(self):
  tree=self.tree(setup.REVISION)
  names=('.DS_Store','Thumbs.db','desktop.ini','._README.md','._timeline.py')
  for directory in (tree,tree/'calculator',tree/'data'):
   for name in names:(directory/name).write_bytes(b'OS metadata')
  self.assertEqual(pins.identify(tree),setup.REVISION)
  self.assertTrue(setup.setup(self.root)['already_present'])
  # The exception cannot conceal damage to a required file.
  (tree/'calculator/timeline.py').write_text('modified calculation')
  with self.assertRaisesRegex(ValueError,'Unknown or modified installed'):setup.setup(self.root)
 def test_metadata_lookalikes_and_directories_remain_unknown(self):
  tree=self.tree(setup.REVISION)
  for name in ('.DS_Store.py','.ds_store','Thumbs.db.bak','Desktop.ini','desktop.ini.py','unknown.py'):
   path=tree/'calculator'/name;path.write_bytes(b'unknown')
   with self.subTest(name=name),self.assertRaisesRegex(ValueError,'Unknown or modified installed'):pins.identify(tree)
   path.unlink()
  path=tree/'._directory';path.mkdir()
  with self.assertRaisesRegex(ValueError,'Unknown or modified installed'):pins.identify(tree)
 def test_product_starts_and_dispatches_with_finder_metadata(self):
  # Use real required engine files and real catalogue data, not executable stubs.
  tree=self.root/'research/upstream/nikke-calc-master'
  for name in PRODUCTION[setup.REVISION]['required']:
   target=tree/name;target.parent.mkdir(parents=True,exist_ok=True)
   shutil.copyfile(self.worker.ENGINE/name,target)
  data=self.root/'data';data.mkdir()
  for source in (ROOT/'data').glob('*.json'):shutil.copyfile(source,data/source.name)
  (tree/'.DS_Store').write_bytes(b'Finder metadata')
  (tree/'calculator/._timeline.py').write_bytes(b'AppleDouble metadata')
  namespace=dict(__file__=str(self.root/'app/engine_worker.py'),__name__='product_startup_metadata_test')
  with patch.object(pins,'REVISIONS',PRODUCTION),patch.object(pins,'verify_tree',side_effect=AssertionError('Product must only use verify_runtime')),patch.object(sys,'path',list(sys.path)):
   exec(compile((ROOT/'app/engine_worker.py').read_text(),'engine_worker.py','exec'),namespace)
   catalog=namespace['dispatch']({'action':'catalog'})
   self.assertEqual(catalog['revision'],setup.REVISION);self.assertTrue(catalog['characters'])
   (tree/'calculator/timeline.py').write_text('modified calculation')
   with self.assertRaisesRegex(ValueError,'revision mismatch'):namespace['evaluate']({})
 def test_existing_backup_collision_preserves_both_trees(self):
  tree=self.tree(setup.HISTORICAL_REVISION);backup=self.tree(setup.HISTORICAL_REVISION,'nikke-calc-23164e4')
  before=self.snapshot(tree);other=self.snapshot(backup)
  with self.assertRaisesRegex(ValueError,'destination already exists'):setup.setup(self.root,self.archive())
  self.assertEqual(self.snapshot(tree),before);self.assertEqual(self.snapshot(backup),other)
 def test_bad_new_archive_does_not_move_old_install(self):
  tree=self.tree(setup.HISTORICAL_REVISION);before=self.snapshot(tree)
  with self.assertRaisesRegex(ValueError,'archive bytes differ'):setup.setup(self.root,self.archive(changes={'calculator/timeline.py':b'changed'}))
  self.assertEqual(self.snapshot(tree),before);self.assertFalse((tree.parent/'nikke-calc-23164e4').exists())
 def test_failed_publication_restores_old_install(self):
  tree=self.tree(setup.HISTORICAL_REVISION);before=self.snapshot(tree);archive=self.archive();original=Path.rename
  def fail_new(path,target):
   if path.name==setup.PREFIX:raise OSError('publication failed')
   return original(path,target)
  with patch.object(Path,'rename',fail_new),self.assertRaisesRegex(OSError,'publication failed'):setup.setup(self.root,archive)
  self.assertEqual(self.snapshot(tree),before)
 def test_fresh_historical_install_uses_explicit_local_archive(self):
  result=setup.setup(self.root,self.archive(),historical=True,historical_archive_path=self.archive(setup.HISTORICAL_REVISION))
  historical=Path(result['historical']['engine']);self.assertEqual(pins.identify(historical),setup.HISTORICAL_REVISION)
  self.assertTrue(setup.setup(self.root,historical=True)['historical']['already_present'])
 def test_historical_pinned_hash_mismatch_is_refused(self):
  self.tree(setup.REVISION);archive=self.archive(setup.HISTORICAL_REVISION,changes={'data/parsed_skills.json':b'changed'})
  with self.assertRaisesRegex(ValueError,'archive bytes differ'):setup.setup(self.root,historical=True,historical_archive_path=archive)
  self.assertFalse((self.root/'research/upstream/nikke-calc-23164e4').exists())
 def test_historical_archive_requires_explicit_option(self):
  with self.assertRaisesRegex(ValueError,'requires --historical'):setup.setup(self.root,historical_archive_path=self.root/'unused.zip')
 def test_unsafe_archive_paths_and_wrong_comments_are_refused(self):
  for revision,extra,symlink in [('wrong',None,False),(setup.REVISION,setup.PREFIX+'/../escaped',False),(setup.REVISION,'/absolute',False),(setup.REVISION,setup.PREFIX+'/linked',True)]:
   with self.subTest(extra=extra,comment=revision),self.assertRaises(ValueError):setup.setup(self.root,self.archive(comment=revision,extra=extra,symlink=symlink))
  self.assertFalse((self.root/'research/upstream/nikke-calc-master').exists())
 def test_duplicate_archive_member_is_refused(self):
  with self.assertRaisesRegex(ValueError,'archive path'):setup.setup(self.root,self.archive(duplicate=True))
 def test_startup_returns_explicit_error_before_upstream_import(self):
  self.tree(setup.HISTORICAL_REVISION);output=io.StringIO();source=(ROOT/'app/engine_worker.py').read_text()
  with contextlib.redirect_stdout(output),self.assertRaises(SystemExit) as error:
   exec(compile(source,'engine_worker.py','exec'),dict(__file__=str(self.root/'app/engine_worker.py'),__name__='__main__'))
  self.assertEqual(error.exception.code,1);self.assertIn('Pinned reference engine revision mismatch',json.loads(output.getvalue())['error'])
 def test_imported_product_refuses_wrong_or_changed_engine_before_evaluation(self):
  tree=self.tree(setup.HISTORICAL_REVISION)
  with patch.object(self.worker,'ENGINE',tree),self.assertRaisesRegex(ValueError,'revision mismatch'):self.worker.evaluate({})
  # A change outside the four headline fingerprints must also be detected.
  for name,data in self.contents[setup.REVISION].items():(tree/name).write_bytes(data)
  (tree/'calculator/damage.py').write_text('modified calculation')
  with patch.object(self.worker,'ENGINE',tree),self.assertRaisesRegex(ValueError,'calculator/damage.py'):self.worker.evaluate({})
 def test_historical_manifest_contains_the_existing_reference_pins(self):
  from historical_engine_reference import PINS
  self.assertEqual({n:PRODUCTION[setup.HISTORICAL_REVISION]['files'][n] for n in PINS},PINS)

if __name__=='__main__':unittest.main()
