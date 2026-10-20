"""Single authored attack-time witness; retain before native comparison,no retry."""
import array,datetime,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import portable_runtime as rt
from portable_enemy_target_oracle import observe
s=importlib.util.spec_from_file_location('time_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
assert not (R/'research/portable-enemy-target-time-initial-finding.json').exists(),'Initial witness already retained;use canonical regression for the fix'
c=next(c for c in v.fixtures() if c['name']=='enemy-source-time-between-frames');program=v.compile_case(c)
f=R/'research/portable-build'/('enemy-target-time-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));f.mkdir();(f/'input.bin').write_bytes(rt.pack_programs([program]))
raw,e=rt.dispatch_programs([program],backend='metal');(f/'readback.bin').write_bytes(raw);(f/'evidence.json').write_text(json.dumps(e,indent=2)+'\n')
for path,digest in e['source_sha256'].items():
 b=(R/path).read_bytes();assert hashlib.sha256(b).hexdigest()==digest;p=f/'source'/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
out=array.array('I');out.frombytes(raw)
if sys.byteorder!='little':out.byteswap()
gpu=rt.decode(out,program[1]);native=observe(c);assert [x['targets'] for x in native['selection']]==[[0],[1]]
report=dict(passed=gpu['enemy_selection']==native['selection'],stage='readback-before-assertion',case=c,gpu=gpu,native=native,captured=str(f),no_unchanged_gpu_retry=True,production_verification_not_complete=True,**e)
(R/'research/portable-enemy-target-time-initial-finding.json').write_text(json.dumps(report,indent=2)+'\n')
print('GPU targets',[x['targets'] for x in gpu['enemy_selection']],'native',[x['targets'] for x in native['selection']])
assert report['passed'],'Attack-time source reference mismatch retained;fix required before full verification'
