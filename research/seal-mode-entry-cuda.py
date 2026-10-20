"""Verify transferred CUDA blobs against fixed-source Metal; never launch a GPU."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
SOURCE='39bce8aa5c9c5f29f0653e80fc69855f19ad5ad6'


def load(name):return json.loads((ROOT/'research'/(name+'.json')).read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def git_bytes(commit,path):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)


def main(args):
    paths=['research/windows-portable-mode-entry-v76.json','research/portable-mode-entry-v76-execution.json']
    changed=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',args.artifact_commit],cwd=ROOT,text=True).splitlines()
    assert changed==sorted(paths)
    assert subprocess.check_output(['git','rev-parse',args.artifact_commit+'^'],cwd=ROOT,text=True).strip()==SOURCE
    sizes=[args.report_bytes,args.execution_bytes];expected=[args.report_sha256,args.execution_sha256]
    for path,size,digest in zip(paths,sizes,expected):
        data=(ROOT/path).read_bytes();assert len(data)==size and sha(data)==digest and data==git_bytes(args.artifact_commit,path),path
    m=load('portable-combat-metal');w=load('windows-portable-mode-entry-v76');run=load('portable-mode-entry-v76-execution')
    assert m['passed'] and w['passed'] and m['backend']=='metal' and w['backend']=='cuda'
    assert m['gpu_execution_verified'] and w['gpu_execution_verified']
    keys=['source_sha256','validation_sha256','input_sha256','output_sha256','cases','rejected_cases','actual_statuses','expected_statuses','batch_layout']
    keys += [k for k in m if k.endswith('_cpu_regressions') or k.startswith('known_')]
    for key in keys:assert m[key]==w[key],key
    assert len(m['cases'])==3540 and len(m['rejected_cases'])==530 and len(m['mode_entry_cpu_regressions'])==400
    for group in ('source_sha256','validation_sha256'):
        for path,digest in m[group].items():assert sha((ROOT/path).read_bytes())==sha(git_bytes(SOURCE,path))==digest,path
    mp=m['mode_entry_existing_parity'];wp=w['mode_entry_existing_parity']
    for parity in (mp,wp):
        assert parity['passed'] and parity['source_commit']==SOURCE and parity['compute_worktree_clean']
        assert parity['prior_inputs']==3539 and parity['current_inputs']==4070 and parity['all_old_output_words_equal']
        assert not parity['changed'] and parity['no_output_normalization'] and parity['no_gpu_retry']
        assert parity['driver_sha256']==sha(git_bytes(SOURCE,'research/verify-mode-entry-regression.py'))
    assert mp['gpu_execution_reused'] and not wp['gpu_execution_reused']
    for key in wp:assert run[key]==wp[key],key
    execution=run['execution']
    assert execution['commit']==SOURCE and execution['exit_code']==0 and not execution['timed_out']
    assert execution['below_normal_priority'] and execution['timeout_seconds']==150
    assert run['actual_gpu_execution_count']==1 and run['residual_verification_process_count']==0
    assert run['original_head_equal'] and run['original_status_equal'] and run['existing_gpu_service_preserved']
    spec=importlib.util.spec_from_file_location('burst_charge_normalizer',ROOT/'research/seal-stack-increment.py')
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    normalized={}
    for backend,suffix in [('cuda','cu'),('metal','metal')]:
        data=(ROOT/'research/portable-build'/('event_runtime.'+suffix)).read_bytes()
        assert sha(data)==m['generated_sha256'][backend]
        normalized[backend]=helper.normalized(data)
        assert normalized[backend]==run['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
    report=dict(passed=True,source_commit=SOURCE,artifact_commit=args.artifact_commit,
        checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),artifact_transfer_complete=True,
        remote_publication_turn=args.remote_turn,remote_turn_status='completed',windows_execution_terminal=True,
        windows_execution=execution,actual_windows_gpu_verification_sessions=1,remaining_verification_processes=0,
        core_programs=4070,positive_cases=3540,rejections=530,hp_attack_native_cases=185,mode_entry_native_cases=400,pending_reference_native_cases=120,
        cuda_dispatch_counts=[d['transport']['cases'] for d in w['dispatches']],metal_dispatch_counts=[d['transport']['cases'] for d in m['dispatches']],
        input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],compared_keys=keys,
        report_sha256=expected[0],execution_sha256=expected[1],normalized_generated_sha256=normalized,
        initial_unlocalized_metal_finding_open=True,full_goal_complete=False,
        scope='Fresh fixed-source CUDA4070 core inputs versus fresh,source-identical Metal capture. Mac-only broad suites,80 physical damage and20 conditional-HP component inputs are separate;no fresh current-source CUDA claim for those suites.')
    (ROOT/'research/portable-mode-entry-transfer-completed.json').write_text(json.dumps(report,indent=2)+'\n')
    if args.timing_order:
        broad=load('portable-mode-entry-broad-validation')
        assert broad['passed'] and broad['all_current_gates_passed'] and broad['mac_gates']==47 and broad['source_commit']==SOURCE
        subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=ROOT,check=True)
        processes=[]
        for line in subprocess.check_output(['ps','-axo','pid=,ppid=,etime=,command='],text=True).splitlines():
            parts=line.split(None,3)
            if len(parts)!=4:continue
            pid,ppid,elapsed,command=parts
            if int(pid)==os.getpid() or ' - <<' in command or command.startswith(('/bin/zsh','/bin/bash')):continue
            if any(x in command for x in [' research/run-',' research/verify-',' scripts/verify-portable-','/scripts/run-metal-probe.swift',' research/benchmark-',' research/capture-']):
                processes.append(dict(pid=int(pid),ppid=int(ppid),elapsed=elapsed,command=command))
        assert not processes,processes
        path=ROOT/'research/portable-mode-entry-timing-order.json';assert not path.exists()
        path.write_text(json.dumps(dict(passed=True,source_commit=SOURCE,checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            mac_gates=47,all_current_mac_gates_complete=True,windows_execution_and_transfer_terminal=True,
            verification_processes=processes,transfer=report,initial_unlocalized_metal_finding_open=True),indent=2)+'\n')
    print('CUDA/Metal4070 input bytes,all output words and native regressions match;transferred Git blobs verified')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--artifact-commit',required=True);parser.add_argument('--report-sha256',required=True)
    parser.add_argument('--report-bytes',type=int,required=True);parser.add_argument('--execution-bytes',type=int,required=True);parser.add_argument('--execution-sha256',required=True);parser.add_argument('--remote-turn',required=True);parser.add_argument('--timing-order',action='store_true')
    main(parser.parse_args())
