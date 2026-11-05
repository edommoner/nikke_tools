"""Test-only readback observer around the original worker dispatch; math is unchanged."""
import json,os,sys
from pathlib import Path
ROOT=Path(os.environ['NIKKE_HTTP_TEST_ROOT']);sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
import engine_worker,portable_runtime as runtime
assert len(sys.argv)==2 and Path(sys.argv[1]).resolve()==(ROOT/'app/engine_worker.py').resolve()
folder=Path(os.environ['NIKKE_HTTP_CAPTURE_DIR']);original=runtime.dispatch_programs;calls=0

def captured(programs,**kwargs):
 global calls
 calls+=1;assert calls==1
 (folder/'input.bin').write_bytes(runtime.pack_programs(programs))
 raw,evidence=original(programs,**kwargs)
 (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 return raw,evidence
runtime.dispatch_programs=captured
if __name__=='__main__':
 try:
  body=json.load(sys.stdin);assert body['action']=='evaluate_portable_events'
  result=engine_worker.dispatch(body)
  print(json.dumps(result,ensure_ascii=True,allow_nan=False))
 except (Exception,SystemExit) as error:
  print(json.dumps({'error':str(error)},ensure_ascii=True));sys.exit(1)
