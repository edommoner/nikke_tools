"""Compact exact comparisons while complete reports/raw remain on each host."""
import argparse,hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXPECTED=ROOT/'research/portable-cross-v79-expected.json'

def load(path):return json.loads(Path(path).read_text())
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def file_sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def normalized(raw):
 text=raw.decode().replace('\r\n','\n').replace('\r','\n');text='\n'.join(x for x in text.split('\n') if not re.match(r'^\s*#line\b',x))
 return hashlib.sha256(re.sub(r'(?m)^#include "[^"\n]*slang-cuda-prelude.h"','#include "slang-cuda-prelude.h"',text).encode()).hexdigest()
def semantic_core(core):
 keys=['cases','rejected_cases','actual_statuses','expected_statuses','batch_layout','resolved_native_hp_differences','application_event_runtime_connected','weapon_burst_target_connected','autonomous_battle_connected','gpu_timeline_connected','cpu_trace_used_as_gpu_input','scope','duplicate_results_verified']
 keys+=sorted(k for k in core if k.endswith('_cpu_regressions') or k.startswith('known_'))
 return {k:dict(sha256=digest(core[k]),entries=len(core[k]) if isinstance(core[k],(list,dict)) else None) for k in keys}
def fingerprint(core,world):
 c=core;w=world['evidence'];p=core['enemy_target_existing_parity'];parity_keys=['passed','all_old_output_words_equal','prior_inputs','current_inputs','current_positive_inputs','prior_input_sha256','prior_output_sha256','projected_input_sha256','projected_output_sha256','changed','no_output_normalization','adoption4658_parity']
 generated={}
 for name,stem,evidence in [('core','event_runtime',c),('world','world_frame_entry',w)]:
  generated[name]={}
  for backend,suffix in [('cuda','cu'),('metal','metal')]:
   capture=Path(core['enemy_target_existing_parity']['raw_path']).parent if name=='core' else Path(world['captured'])
   expected_sha=evidence['generated_sha256'][backend]
   snapshot=ROOT/'research/portable-build/generated-proof'/stem/(expected_sha+'.'+suffix)
   candidates=[snapshot,capture.parent/(stem+'.'+suffix),ROOT/'research/portable-build'/(stem+'.'+suffix)]
   path=next((p for p in candidates if p.exists() and file_sha(p)==expected_sha),None)
   assert path is not None,('No exact generated source for saved report',name,backend,expected_sha)
   raw=path.read_bytes()
   if not snapshot.exists():
    snapshot.parent.mkdir(parents=True,exist_ok=True);snapshot.write_bytes(raw)
   generated[name][backend]=normalized(raw)
 return dict(core_input_sha256=c['input_sha256'],core_output_sha256=c['output_sha256'],core_source_sha256=c['source_sha256'],core_validation_sha256=c['validation_sha256'],core_semantic_fields=semantic_core(c),core_existing_parity={k:p[k] for k in parity_keys},world_input_sha256=w['input_sha256'],world_output_sha256=w['output_sha256'],world_source_sha256=w['source_sha256'],world_cases_sha256=digest(world['cases']),world_golden_sha256=world['golden_sha256'],generated_normalized_sha256=generated)
def observed(core,world):
 return dict(core_passed=core['passed'],world_passed=world['passed'],positive_cases=len(core['cases']),negative_cases=len(core['rejected_cases']),world_cases=len(world['cases']),core_gpu_execution_verified=core['gpu_execution_verified'],world_gpu_execution_verified=world['evidence']['gpu_execution_verified'],core_transport=core['transport'],world_transport=world['evidence']['transport'],core_report_source_commit=core['enemy_target_existing_parity']['source_commit'],world_report_source_commit=world['source_commit'])

def main():
 p=argparse.ArgumentParser();p.add_argument('--core',type=Path,required=True);p.add_argument('--world',type=Path,required=True);p.add_argument('--make-expected',action='store_true');p.add_argument('--expected',type=Path,default=EXPECTED);p.add_argument('--backend',choices=('metal','cuda'),default='cuda');p.add_argument('--out',type=Path);args=p.parse_args()
 core=load(args.core);world=load(args.world);actual=fingerprint(core,world);facts=observed(core,world)
 valid=facts['core_passed'] and facts['world_passed'] and facts['positive_cases']==4112 and facts['negative_cases']==570 and facts['world_cases']==49 and facts['core_gpu_execution_verified'] and facts['world_gpu_execution_verified']
 if args.make_expected:
  assert valid and core['transport']['backend']=='metal' and world['evidence']['transport']['backend']=='metal'
  result=dict(passed=True,comparison=actual,observed=facts,summary_driver_sha256=file_sha(__file__),scope='Actual same-source Metal core4682 and world49 results. Full report dictionaries and all output bytes are fingerprinted;source/raw reports stay on their originating host.',full_character_verified=0,full_goal_complete=False)
  args.expected.write_text(json.dumps(result,indent=2)+'\n');print('Saved exact Metal comparison fingerprints',args.expected);return
 expected=load(args.expected);changed=[k for k in set(actual)|set(expected['comparison']) if actual.get(k)!=expected['comparison'].get(k)]
 backend_ok=core['transport']['backend']==args.backend and world['evidence']['transport']['backend']==args.backend
 result=dict(passed=bool(valid and backend_ok and not changed and file_sha(__file__)==expected['summary_driver_sha256']),changed_keys=sorted(changed),comparison=actual,observed=facts,expected_sha256=file_sha(args.expected),source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),backend=args.backend,scope='Exact full-output and full semantic-dictionary SHA256 comparison. This compact report does not discard or replace detailed reports/raw retained on this host.',full_character_verified=0,full_goal_complete=False,normal_ui='CPU')
 out=args.out or ROOT/f'research/portable-cross-v79-{args.backend}-summary.json';out.write_text(json.dumps(result,indent=2)+'\n')
 assert result['passed'],dict(changed=changed,backend_ok=backend_ok,valid=valid)
 print('Core4682 and world49 exact fingerprints match',args.backend)
if __name__=='__main__':main()
