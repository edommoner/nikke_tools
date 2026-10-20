"""Exact decimal uint64 seed through a fresh loopback HTTP server; no UI service restart."""
import argparse,copy,datetime,os,shlex,hashlib,importlib.util,json,select,shutil,subprocess,sys,time,urllib.error,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'app'),str(R/'scripts')]
import engine_worker,portable_runtime as runtime
from portable_specs import LIMITS as L
from timer_registry_cases import NAMES

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=['metal','cuda'],default='metal');a=p.parse_args()
 report=json.loads((R/f'research/portable-combat-{a.backend}.json').read_text());assert report['passed']
 spec=importlib.util.spec_from_file_location('http_target_core',R/'scripts/verify-portable-combat.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
 case=next(c for c in v.fixtures() if c['name']=='enemy-decimal-seed-18446744073709551615');program=v.compile_case(case)
 chars=[dict(name=n,skill_levels={'1':10,'2':10,'3':10},_weapon=dict(engine_worker.META[n])) for n in NAMES]
 for char,w in zip(chars,case['combat']['weapons']):char['_weapon']['reload_time']=w.get('reload',1)
 environment=copy.deepcopy(case.get('environment',{}));environment['enemy_targeting']=copy.deepcopy(case['enemy_targeting'])
 body=dict(chars=chars,effects=[dict(effect=e,owner=NAMES[o]) for e,o in zip(case['effects'],case['owners'])],script=case['script'],base_atk=case['base_atk'],combat=case['combat'],environment=environment,backend=a.backend)
 index=next(i for i,c in enumerate(report['cases']) if c['name']==case['name']);expected=report['cases'][index]['actual']
 input_sha=hashlib.sha256(runtime.pack_programs([program])).hexdigest()
 raw_path=Path(report['enemy_target_existing_parity']['raw_path'])
 with raw_path.open('rb') as stream:stream.seek(index*L['OUTPUT_WORDS']*4);block=stream.read(L['OUTPUT_WORDS']*4)
 assert len(block)==L['OUTPUT_WORDS']*4;output_sha=hashlib.sha256(block).hexdigest()
 code="import {server} from './server.mjs'; server.listen(0,'127.0.0.1',()=>console.log(server.address().port)); process.on('SIGTERM',()=>server.close(()=>process.exit(0)));"
 log=Path('/tmp/nikke-enemy-target-http-server.log');child=None;result={}
 captured=R/'research/portable-build'/('enemy-target-http-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));captured.mkdir()
 wrapper=captured/'python-observer';wrapper.write_text('#!/bin/sh\nexec '+shlex.quote(sys.executable)+' '+shlex.quote(str(R/'research/capture-enemy-target-http-worker.py'))+' "$@"\n');wrapper.chmod(0o755)
 environment_process=dict(os.environ,NIKKE_PYTHON=str(wrapper),NIKKE_HTTP_TEST_ROOT=str(R),NIKKE_HTTP_CAPTURE_DIR=str(captured))
 try:
  with log.open('w') as errors:
   child=subprocess.Popen([shutil.which('node'),'--input-type=module','-e',code],cwd=R,stdout=subprocess.PIPE,stderr=errors,text=True,env=environment_process)
   ready,_,_=select.select([child.stdout],[],[],30);assert ready,'Test server did not become ready'
   port=int(child.stdout.readline().strip());url=f'http://127.0.0.1:{port}/api/portable-events'
   # Unsafe numeric input must be rejected by Node before compiling or running any GPU code.
   malformed=b'{"environment":{"enemy_targeting":{"seed":9007199254740993}}}'
   try:urllib.request.urlopen(urllib.request.Request(url,data=malformed,headers={'Content-Type':'application/json'}),timeout=10)
   except urllib.error.HTTPError as error:
    rejection=json.loads(error.read());assert error.code==400 and '乱数種' in rejection['error']
   else:raise AssertionError('Unsafe JSON numeric seed reached the worker')
   data=json.dumps(body,ensure_ascii=False).encode();response=urllib.request.urlopen(urllib.request.Request(url,data=data,headers={'Content-Type':'application/json'}),timeout=660)
   actual=json.load(response)
   # Preserve the complete HTTP response before asserting transport or decoded parity.
   destination=R/f'research/portable-enemy-target-http-{a.backend}.json'
   result=dict(passed=False,case=case['name'],seed_wire_encoding='canonical unsigned decimal text',seed_text=environment['enemy_targeting']['seed'],source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),expected_input_sha256=input_sha,expected_output_sha256=output_sha,response=actual,rejected_unsafe_numeric_seed=rejection,test_server_pid=child.pid,test_server_port=port,original4317_service_restarted=False,captured=str(captured),observer_changes_math=False)
   destination.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
   assert actual['gpu_execution_verified'] and actual['backend']==a.backend and len(actual['results'])==1
   assert actual['input_sha256']==input_sha and actual['output_sha256']==output_sha
   assert hashlib.sha256((captured/'input.bin').read_bytes()).hexdigest()==input_sha
   assert (captured/'readback.bin').read_bytes()==block
   assert actual['results'][0]==expected,'HTTP must preserve complete canonical decoded result'
   result['passed']=True
 finally:
  if child is not None:
   child.terminate()
   try:child.wait(timeout=10)
   except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
   if result:
    result['test_server_exited']=True;result['test_server_exit_code']=child.returncode
    result['validation_sha256']={p:hashlib.sha256((R/p).read_bytes()).hexdigest() for p in ('server.mjs','app/portable_http_policy.mjs','app/portable_enemy_target_specs.py','research/verify-enemy-target-http.py','research/capture-enemy-target-http-worker.py','tests/portable-http-policy.test.mjs')}
    (R/f'research/portable-enemy-target-http-{a.backend}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('Decimal uint64 seed HTTP input/output/decoded result exact;unsafe numeric rejected;test server stopped')
if __name__=='__main__':main()
