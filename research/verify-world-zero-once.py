"""Distinct sub-EPS initial-zero cases through the common CUDA/Metal entry."""
import argparse,array,copy,datetime,hashlib,importlib.util,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
from portable_backend import execute,source_hashes
spec=importlib.util.spec_from_file_location('world_frame',ROOT/'research/verify-world-frame.py');f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)

def fixtures():
 base=copy.deepcopy(f.fixtures()[0]);base['duration']=.05;base['patterns'][0]['spec']['hits']=1;base['patterns'][0]['until']=dict(time=5e-10);base['name']='initial-zero-once-sub-epsilon-expiry';rows=[base]
 c=copy.deepcopy(base);c['name']='initial-zero-once-sub-epsilon-repeat';c['patterns'][0].update(after=['start','a'],repeat=0);rows.append(c)
 c=copy.deepcopy(base);c['name']='initial-zero-once-sub-epsilon-follow';c['patterns']=[dict(id='wait',kind='idle',until=dict(time=5e-10)),dict(c['patterns'][0],id='a',after=['wait'])];rows.append(c)
 c=copy.deepcopy(base);c['name']='initial-zero-once-zero-duration-finish';c['duration']=0;rows.append(c)
 return rows

def main():
 p=argparse.ArgumentParser();p.add_argument('--backend',choices=('metal','cuda'),default='metal');p.add_argument('--replay',type=Path);args=p.parse_args()
 cases=fixtures();compiled=[f.compile_case(c) for c in cases];data=array.array('I',[len(cases)])
 for words,_ in compiled:data.extend(words)
 if sys.byteorder!='little':data.byteswap()
 packed=data.tobytes();source='gpu/world_frame_entry.slang'
 if args.replay:
  folder=args.replay.resolve();raw=(folder/'readback.bin').read_bytes();evidence=json.loads((folder/'evidence.json').read_text())
  assert (folder/'input.bin').read_bytes()==packed and evidence['source_sha256']==source_hashes(source)
  assert evidence['backend']==args.backend and evidence['gpu_execution_verified'] and hashlib.sha256(raw).hexdigest()==evidence['output_sha256']
 else:
  folder=ROOT/'research/portable-build'/('world-zero-once-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));folder.mkdir(parents=True);(folder/'input.bin').write_bytes(packed)
  raw,evidence=execute(source,'portableEvents',packed,f.L['WORLD_FRAME_INPUT_WORDS'],f.L['WORLD_FRAME_OUTPUT_WORDS'],args.backend)
  (folder/'readback.bin').write_bytes(raw);(folder/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 values=array.array('I');values.frombytes(raw)
 if sys.byteorder!='little':values.byteswap()
 rows=[];stride=f.L['WORLD_FRAME_OUTPUT_WORDS'];keys=('damage','allies','covers','shots','ammo','hits','boss_log','rng','graph_states','graph_history')
 for i,(case,(_,meta)) in enumerate(zip(cases,compiled)):
  actual=f.read_result(values[i*stride:(i+1)*stride],meta,case);native=f.observe(case);differences=[k for k in keys if actual[k]!=native[k]]
  rows.append(dict(name=case['name'],passed=actual['status']==0 and not differences,differences=differences,actual=actual,native=native))
 report=dict(passed=all(r['passed'] for r in rows),cases=rows,captured=str(folder),evidence=evidence,source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),gpu_execution_reused=args.replay is not None,full_character_verified=0,canonical_world_admission=False,full_goal_complete=False,normal_ui='CPU',scope='Full native fields for initial-zero-once sub-EPS expiry/repeat/follow and duration0. Shared CUDA/Metal source and fixtures;original failed source/raw retained separately.')
 (ROOT/f'research/portable-world-zero-once-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert report['passed'],[(r['name'],r['differences']) for r in rows if not r['passed']]
 print(len(rows),'initial-zero-once cases match full native simulate',args.backend)
if __name__=='__main__':main()
