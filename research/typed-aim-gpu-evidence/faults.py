import array,copy,importlib.util,json,sys
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root/p) for p in ('app','research','scripts')]
s=importlib.util.spec_from_file_location('aim_fault_cli',root/'scripts/nikke_gpu.py');cli=importlib.util.module_from_spec(s);s.loader.exec_module(cli)
m=cli.verify_package(root)
with cli.forbid_gpu():
 adapter=cli.open_suite(m);entries,_=cli.prepare_entries(adapter,m);name,_,d=entries[52];n=adapter.native_reference(d)
 with Path('/tmp/nikke-typed-aim-metal-v3/readback.bin').open('rb') as f:f.seek(52*2032000*4);block=array.array('I');block.frombytes(f.read(2032000*4))
 from portable_coordinate_typed_aim_comparison import compare,HEAD,END
 from portable_specs import LIMITS as L
 from portable_coordinate_aim_wire import LAYOUT as A
 s=importlib.util.spec_from_file_location('aim_fault_legacy',root/'research/verify-coordinate-aim-short.py');legacy=importlib.util.module_from_spec(s);s.loader.exec_module(legacy)
 compare(block,d,n);legacy.compare_aim(block,d,n['coordinate_aim'])
 assert block[A['STATE']+32]==256
 packed=block[L['FOCUS_STATE_BASE']]|block[L['FOCUS_STATE_BASE']+1]<<32;assert packed&511==256
 faults=[('candidate-generation',HEAD+33,compare),('candidate-stream-digest',HEAD+8,compare),('last-candidate-id',HEAD+3,compare),('nine-bit-focus',L['FOCUS_STATE_BASE'],compare),('unused-aim-tail',END,compare),('resolved-frame-digest',A['STATE']+4,lambda b,d,n:legacy.compare_aim(b,d,n['coordinate_aim']))]
 result=[]
 for label,at,check in faults:
  bad=array.array('I',block);bad[at]^=1
  try:check(bad,d,n)
  except AssertionError:result.append(dict(fault=label,offset=at,rejected=True))
  else:raise AssertionError('Accepted corruption: '+label)
 r=dict(case=name,retained_gpu_status=block[0],last_typed_aim_id=block[A['STATE']+32],last_focus_id=packed&511,checks=result,fresh_native_cases=1,gpu_calls=0)
 Path('/tmp/nikke-typed-aim-faults-v1.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
