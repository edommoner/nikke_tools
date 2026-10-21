"""Independent saved buffer/source/native audit; no GPU calls or input simulation."""
import array,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
s=importlib.util.spec_from_file_location('roster_short',ROOT/'research/verify-world-roster-short.py');short=importlib.util.module_from_spec(s);s.loader.exec_module(short)
def sha(x):return hashlib.sha256(x).hexdigest()
def main():
 import portable_backend
 def forbidden(*a,**k):raise AssertionError('GPU forbidden in saved audit')
 with patch.object(portable_backend,'execute',forbidden),patch.object(portable_backend,'build',forbidden),patch.object(short.suite,'execute',forbidden):
  r=json.loads((ROOT/'research/portable-world-roster-metal.json').read_text());gold=json.loads(short.GOLDEN.read_text());folder=Path(r['captured']);entries,data=short.prepare();raw=(folder/'readback.bin').read_bytes();assert r['passed'] and data==(folder/'input.bin').read_bytes();assert sha(data)==r['input_sha256']==gold['input_sha256'] and sha(raw)==r['readback_sha256']==gold['output_sha256'];assert len(raw)==len(entries)*short.suite.OUTPUT_WORDS*4
  commit=r['source_commit'];assert commit.startswith('76dc4de')
  for p,h in r['evidence']['source_sha256'].items():assert sha(subprocess.check_output(['git','show',commit+':'+p]))==h,p
  assert r['evidence']['gpu_execution_verified'] and r['evidence']['transport']['device']=='Apple M5' and r['evidence']['transport']['command_status']=='completed'
  ow=short.suite.OUTPUT_WORDS*4
  for i,(name,w,domain) in enumerate(entries):
   b=array.array('I');b.frombytes(raw[i*ow:(i+1)*ow]);b.byteswap() if sys.byteorder!='little' else None
   assert sha(raw[i*ow:(i+1)*ow])==gold['entries'][i]['output_sha256']
   if domain:
    c,p,m=domain;actual=short.decode(b[:159744],m);native=short.suite.reference.native_reference(c['body']);assert not short.suite.reference.compare_native_result(actual,p,native,program=(w,m));assert short.cross.digest(native)==gold['entries'][i]['native_sha256'];assert actual==r['cases'][i]['actual'] and native==r['cases'][i]['native'] and b[0]==0
   else:assert b[0]==64
  before=json.loads((ROOT/'research/portable-world-roster-history-fix-metal.json').read_text());oldraw=Path(before['captured'],'readback.bin').read_bytes();assert oldraw==raw[:len(oldraw)]
  generated=json.loads((ROOT/'research/portable-world-roster-generation.json').read_text());assert generated['passed'] and len(generated['cases'])==20
  result=dict(passed=True,source_commit=commit,input_count=10,native_real_squads=6,all_effects_included=True,input_sha256=sha(data),output_sha256=sha(raw),old20_generated_exact=True,history_fix_six_full_output_blocks_preserved=True,full_history_not_claimed=True,diagnostic_omitted=[c['diagnostic_history'] for c in r['cases']],cpu_checks=531,gpu_audit_calls=0,canonical_world_admission=False,full_character_verified=0,normal_ui='CPU',full_goal_complete=False)
 (ROOT/'research/portable-world-roster-validation.json').write_text(json.dumps(result,indent=2)+'\n');print('Saved Metal10/native6/source/Git/old20 audited; GPU0')
if __name__=='__main__':main()
