"""Join exact new CUDA component bytes with unchanged saved CUDA evidence.

Old2503 were not executed again. The full current Metal readback covers2754;
the current CUDA component covers251, with exact saved input/source reuse for
the remainder. No decoded-output reconstruction substitutes for raw parity.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess

ROOT=Path(__file__).resolve().parents[1];P=ROOT/'research'
SOURCE='795a9e5b684796b3b6a2fb9b59546e60401a5503'


def load(name):return json.loads((P/(name+'.json')).read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def git(commit,path):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
def save(name,value):(P/(name+'.json')).write_text(json.dumps(value,indent=2)+'\n')


def blocks_sha(path,indices,stride,header=0,include_count=False):
    digest=hashlib.sha256()
    if include_count:digest.update(struct.pack('<I',len(indices)))
    with path.open('rb') as f:
        for index in indices:
            f.seek(header+index*stride);block=f.read(stride);assert len(block)==stride
            digest.update(block)
    return digest.hexdigest()


def main(args):
    m=load('portable-combat-metal');w=load('windows-portable-target-states-v71')
    incremental=load('portable-target-states-incremental-cuda-parity')
    paths=['research/windows-portable-target-states-v71.json','research/portable-target-states-incremental-cuda-parity.json']
    assert subprocess.check_output(['git','rev-parse',args.artifact_commit+'^'],cwd=ROOT,text=True).strip()==SOURCE
    changed=subprocess.check_output(['git','diff-tree','--no-commit-id','--name-only','-r',args.artifact_commit],cwd=ROOT,text=True).splitlines()
    assert changed==sorted(paths)
    for path,digest in zip(paths,[args.windows_sha256,args.parity_sha256]):
        assert sha((ROOT/path).read_bytes())==digest and (ROOT/path).read_bytes()==git(args.artifact_commit,path)
    assert m['passed'] and w['passed'] and incremental['passed']
    assert m['backend']=='metal' and w['backend']=='cuda' and m['gpu_execution_verified'] and w['gpu_execution_verified']
    assert len(m['cases'])==2363 and len(m['rejected_cases'])==391
    assert len(m['target_state_cpu_regressions'])==233 and len(w['cases'])==233 and len(w['rejected_cases'])==18
    assert w['raw_rejections_verified'] and w['actual_rejection_statuses']==[64]*18
    assert incremental['source_commit']==SOURCE and incremental['verification_mode']=='incremental'
    assert incremental['logical_total_inputs']==2754 and incremental['current_source_actual_gpu_inputs']==251
    assert incremental['source_identical_saved_inputs']==2503 and not incremental['old_gpu_reexecuted']
    assert incremental['compute_worktree_clean'] and incremental['no_output_normalization']
    assert incremental['driver_sha256']==sha(git(SOURCE,'research/verify-target-state-incremental-cuda.py'))
    execution,post=w['execution'],w['postcheck']
    assert execution['commit']==SOURCE and execution['exit_code']==0 and not execution['timed_out']
    assert execution['below_normal_priority'] and execution['timeout_seconds']==120
    assert post['residual_verification_process_count']==0 and not post['residual_verification_processes'] and post['existing_gpu_service_preserved']
    for field in ('head','status'):assert execution['original_'+field+'_before']==post['original_'+field+'_after']
    for group in ('source_sha256','validation_sha256'):
        for path,digest in w[group].items():assert sha((ROOT/path).read_bytes())==sha(git(SOURCE,path))==digest,path
    assert m['source_sha256']==w['source_sha256']==incremental['source_sha256']
    reuse=load('portable-target-states-v70-reuse-manifest')
    old=json.loads(git(reuse['prior_artifact_commit'],'research/windows-portable-target-states-v70.json'))
    assert sha(git(reuse['prior_artifact_commit'],'research/windows-portable-target-states-v70.json'))==reuse['prior_report_sha256']
    assert reuse['source_sha256']==old['source_sha256']==w['source_sha256']
    for key in ('input_sha256','output_sha256'):assert reuse[key]==old[key]==incremental['prior_full_'+key]
    assert incremental['retained_output_sha256']==old['target_state_existing_parity']['projected_output_sha256']
    assert incremental['retained_input_abi6d_sha256']==old['target_state_existing_parity']['projected_input_sha256']
    metal_parity=m['target_state_existing_parity']
    assert metal_parity['passed'] and metal_parity['source_commit']==SOURCE and not metal_parity['gpu_execution_reused']
    assert metal_parity['compute_worktree_clean'] and metal_parity['all_old_output_words_equal'] and not metal_parity['changed']
    assert metal_parity['projected_output_sha256']==incremental['retained_output_sha256']
    assert metal_parity['projected_input_sha256']==incremental['retained_input_abi6d_sha256']
    assert m['input_sha256']==incremental['current_full_input_sha256']
    old_indices=list(range(2130))+list(range(2363,2736));new_indices=list(range(2130,2363))+list(range(2736,2754))
    assert incremental['old_indices']==old_indices and incremental['new_indices']==new_indices
    input_path=Path(metal_parity['input_path']);raw_path=Path(metal_parity['raw_path'])
    assert blocks_sha(input_path,new_indices,86016*4,4,True)==w['input_sha256']==incremental['component_input_sha256']
    assert blocks_sha(input_path,old_indices,86016*4,4,True)==incremental['retained_input_sha256']
    assert blocks_sha(raw_path,new_indices,159744*4)==w['output_sha256']==incremental['component_output_sha256']
    assert blocks_sha(raw_path,old_indices,159744*4)==incremental['retained_output_sha256']
    spec=importlib.util.spec_from_file_location('incremental_normalizer',P/'seal-stack-increment.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    normalized={}
    for backend,suffix in [('cuda','cu'),('metal','metal')]:
        data=(P/'portable-build'/('event_runtime.'+suffix)).read_bytes()
        assert sha(data)==m['generated_sha256'][backend]
        normalized[backend]=helper.normalized(data)
        assert normalized[backend]==w['generated_normalization'][backend]['no_line_directives_portable_prelude_sha256']
    transfer=dict(passed=True,source_commit=SOURCE,artifact_commit=args.artifact_commit,
        checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),verification_mode='incremental',
        artifact_transfer_complete=True,windows_execution_terminal=True,remote_turn=args.remote_turn,remote_turn_status='completed',
        current_source_actual_cuda_inputs=251,source_identical_saved_cuda_inputs=2503,logical_core_inputs=2754,
        target_state_native_cases=233,positive_cases=2363,rejections=391,old_gpu_reexecuted=False,
        all_current_input_and_output_bytes_compared=True,remaining_verification_processes=0,
        component_input_sha256=w['input_sha256'],component_output_sha256=w['output_sha256'],
        retained_input_sha256=incremental['retained_input_sha256'],retained_output_sha256=incremental['retained_output_sha256'],
        input_sha256=m['input_sha256'],output_sha256=m['output_sha256'],
        normalized_generated_sha256=normalized,prior_artifact_commit=reuse['prior_artifact_commit'],
        windows_report=paths[0],windows_report_sha256=args.windows_sha256,parity_report_sha256=args.parity_sha256,
        initial_unlocalized_metal_finding_open=True,full_character_verified=0,full_goal_complete=False)
    save('portable-target-states-transfer-completed',transfer)
    if args.timing_order:
        broad=load('portable-target-states-broad-validation')
        assert broad['passed'] and broad['all_current_gates_passed'] and broad['source_commit']==SOURCE and broad['mac_gates']==35
        subprocess.run(['git','diff','--exit-code',SOURCE,'--','app','scripts','gpu','tests'],cwd=ROOT,check=True)
        processes=[]
        for line in subprocess.check_output(['ps','-axo','pid=,ppid=,etime=,command='],text=True).splitlines():
            parts=line.split(None,3)
            if len(parts)!=4:continue
            pid,ppid,elapsed,command=parts
            if int(pid)==os.getpid() or command.startswith(('/bin/zsh','/bin/bash')):continue
            if any(x in command for x in (' research/run-',' research/verify-',' scripts/verify-portable-','/scripts/run-metal-probe.swift',' research/benchmark-',' research/capture-')):
                processes.append(dict(pid=int(pid),command=command))
        assert not processes,processes
        assert not (P/'portable-target-states-timing-order.json').exists()
        save('portable-target-states-timing-order',dict(passed=True,source_commit=SOURCE,
            checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),mac_gates=35,
            all_current_mac_gates_complete=True,windows_execution_and_transfer_terminal=True,
            verification_processes=processes,transfer=transfer))
    print('Current251 CUDA readbacks and retained2503 CUDA bytes match full current2754 Metal inputs/outputs')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--artifact-commit',required=True);parser.add_argument('--windows-sha256',required=True)
    parser.add_argument('--parity-sha256',required=True);parser.add_argument('--remote-turn',required=True)
    parser.add_argument('--timing-order',action='store_true');main(parser.parse_args())
