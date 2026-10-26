"""Only one reviewed host admission line may change; claims/calculation stay frozen."""
import hashlib,json,sys,tempfile,types,unittest,zipfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
import portable_metal_wire_refresh as repair
from portable_wire_layout import metal_guard,LARGE_OUTPUT_WORDS
ROOT=Path(__file__).resolve().parents[1]

def package_id(m):return repair.sha(json.dumps({k:v for k,v in m.items() if k!='package_id'},sort_keys=True,separators=(',',':')).encode())
def write(path,value):path.write_text(json.dumps(value))
def record(root,name):
 raw=(root/name).read_bytes();return dict(path=name,bytes=len(raw),sha256=repair.sha(raw))
def check(root,rows):
 for row in rows:
  raw=(root/row['path']).read_bytes()
  if len(raw)!=row['bytes'] or repair.sha(raw)!=row['sha256']:raise ValueError('Corrupt immutable file')

class MetalWireRefreshTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();root=Path(self.tmp.name);self.addCleanup(self.tmp.cleanup)
  self.source=root/'source';self.capture=root/'capture';self.source.mkdir();self.capture.mkdir();(self.source/'scripts').mkdir();self.output=root/'new.zip'
  current=(ROOT/repair.PATH).read_text(encoding='utf-8');before=current.replace(metal_guard(),metal_guard(LARGE_OUTPUT_WORDS[:-1]))
  self.assertEqual(repair.sha(before.encode()),repair.REVIEWED_OLD_SHA)
  (self.source/repair.PATH).write_bytes(before.encode('utf-8'));(self.source/'oracle.py').write_text('frozen oracle');(self.source/'shader.slang').write_text('frozen arithmetic')
  self.assertEqual(repair.sha((self.source/repair.PATH).read_bytes()),repair.REVIEWED_OLD_SHA)
  (self.source/'tests/fixtures').mkdir(parents=True);write(self.source/repair.LEDGER,dict(sources={},added_sources={}))
  self.manifest=dict(schema=1,suite='coordinate-resident-arc',purpose='development',selected_cases=[],files=[record(self.source,name) for name in [repair.PATH,repair.LEDGER,'oracle.py','shader.slang']],golden=dict(entries=[dict(input_sha256='input',native_sha256='native')],source_sha256={'shader.slang':'frozen'}))
  self.manifest['package_id']=package_id(self.manifest);write(self.source/'gpu-package.json',self.manifest)
  write(self.source/'gpu-claimed-metal.json',dict(capture=str(self.capture),package_id=self.manifest['package_id']))
  write(self.capture/'run.json',dict(package_id=self.manifest['package_id'],backend='metal',mode='gpu',status='finished'))
  write(self.capture/'execution.json',dict(final_child_exit_code=1,timed_out=False,cleanup_error=None));write(self.capture/'result.json',dict(calculation_verified=False))
  (self.capture/'stderr.log').write_text('Invalid wire layout')
  write(self.capture/'comparison.json',dict(calculation_verified=False,comparison_error='Missing readback.bin'));self.collect()
  def verify(root):
   m=json.loads((root/'gpu-package.json').read_text());check(root,m['files'])
   if m['package_id']!=package_id(m):raise ValueError('Bad package ID')
   return m
  self.api=types.SimpleNamespace(verify_saved_package=verify,check_records=check,package_id=package_id)
 def collect(self):write(self.capture/'artifacts.json',dict(files=[record(self.capture,p.name) for p in self.capture.iterdir() if p.name!='artifacts.json']))
 def refresh(self):return repair.refresh(self.api,self.source,self.capture,self.output)
 def test_only_reviewed_swift_line_changes_and_original_claim_remains(self):
  claim=(self.source/'gpu-claimed-metal.json').read_bytes();result=self.refresh();self.assertTrue(result['passed']);self.assertEqual(result['changed_files'],[repair.PATH,repair.LEDGER]);self.assertEqual(result['native_battle_calls'],0)
  self.assertEqual((self.source/'gpu-claimed-metal.json').read_bytes(),claim)
  with zipfile.ZipFile(self.output) as z:
   m=json.loads(z.read('gpu-package.json'));self.assertEqual(m['golden'],self.manifest['golden']);self.assertNotEqual(m['package_id'],self.manifest['package_id'])
   for row in self.manifest['files']:
    if row['path'] not in (repair.PATH,repair.LEDGER):self.assertEqual(z.read(row['path']),(self.source/row['path']).read_bytes())
   self.assertEqual(z.read(repair.PATH),(ROOT/repair.PATH).read_bytes());self.assertEqual(json.loads(z.read(repair.LEDGER))['sources'][repair.PATH]['baseline_sha256'],repair.REVIEWED_OLD_SHA);self.assertNotIn('gpu-claimed-metal.json',z.namelist())
 def test_arbitrary_swift_edits_are_rejected(self):
  with self.assertRaisesRegex(ValueError,'Unreviewed'):repair.replacement((self.source/repair.PATH).read_bytes()+b'\n')
 def test_crlf_bytes_do_not_bypass_the_reviewed_transport_hash(self):
  raw=(self.source/repair.PATH).read_bytes();self.assertNotIn(b'\r\n',raw)
  with self.assertRaisesRegex(ValueError,'Unreviewed'):repair.replacement(raw.replace(b'\n',b'\r\n'))
 def test_started_dispatch_or_saved_output_prevents_refresh(self):
  for name in ['readback.bin','evidence.json']:
   path=self.capture/name;path.write_bytes(b'partial')
   with self.subTest(name=name),self.assertRaisesRegex(ValueError,'Device/dispatch'):self.refresh()
   path.unlink()
  (self.capture/'stderr.log').write_text('Invalid wire layout\nportable_stage=gpu_dispatch')
  with self.assertRaisesRegex(ValueError,'Device/dispatch'):self.refresh()
 def test_unexpected_comparison_is_not_treated_as_no_output(self):
  write(self.capture/'comparison.json',dict(calculation_verified=False,entries=[{}]))
  with self.assertRaisesRegex(ValueError,'comparison evidence'):self.refresh()
 def test_nonterminal_or_successful_capture_prevents_refresh(self):
  write(self.capture/'run.json',dict(package_id=self.manifest['package_id'],backend='metal',mode='gpu',status='running'))
  with self.assertRaisesRegex(ValueError,'terminal'):self.refresh()
 def test_corrupt_saved_artifacts_prevent_refresh(self):
  (self.capture/'stderr.log').write_text('Invalid wire layout\nchanged')
  with self.assertRaisesRegex(ValueError,'Corrupt'):self.refresh()
 def test_existing_output_is_never_overwritten(self):
  self.output.write_text('keep')
  with self.assertRaises(FileExistsError):self.refresh()
  self.assertEqual(self.output.read_text(),'keep')
 def test_different_failure_is_not_repaired(self):
  (self.capture/'stderr.log').write_text('No Metal device');self.collect()
  with self.assertRaisesRegex(ValueError,'different failure'):self.refresh()

if __name__=='__main__':unittest.main()
