"""Execute changed conditions only; prove exact old CUDA bytes/source reuse.

No combined fresh-GPU execution is claimed. The new component and old2503
outputs remain separate and are compared with the full current Metal readback.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from portable_runtime import pack_programs
from portable_specs import LIMITS as L


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


def file_sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as f:
        while part:=f.read(8*1024*1024):digest.update(part)
    return digest.hexdigest()


def programs_sha(programs):
    digest=hashlib.sha256(struct.pack('<I',len(programs)))
    for program in programs:digest.update(pack_programs([program])[4:])
    return digest.hexdigest()


class Captured(BaseException):pass


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--prior-directory',type=Path,required=True)
    parser.add_argument('--preflight-only',action='store_true')
    args=parser.parse_args()
    source=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    subprocess.run(['git','diff','--exit-code',source,'--','app','scripts','gpu','tests'],cwd=ROOT,check=True)
    manifest=json.loads((ROOT/'research/portable-target-states-v70-reuse-manifest.json').read_text())
    prior=json.loads((args.prior_directory/'evidence.json').read_text())
    assert prior['backend']=='cuda' and prior['gpu_execution_verified']
    for field in ('input_sha256','output_sha256','source_sha256'):assert prior[field]==manifest[field],field
    for path,digest in manifest['source_sha256'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==digest,path
    assert file_sha(args.prior_directory/'input.bin')==manifest['input_sha256']
    assert file_sha(args.prior_directory/'readback.bin')==manifest['output_sha256']
    verifier=module('incremental_core','scripts/verify-portable-combat.py')
    programs=[]
    def collect(p,**kwargs):programs.extend(p);raise Captured()
    report=ROOT/'research/portable-combat-cuda.json';saved=report.read_bytes() if report.exists() else None
    argv=sys.argv;sys.argv=[sys.argv[0],'--backend','cuda'];verifier.run_programs=collect
    try:
        try:verifier.main()
        except Captured:pass
    finally:
        sys.argv=argv
        if saved is None:report.unlink(missing_ok=True)
        else:report.write_bytes(saved)
    cases=verifier.fixtures();old_count=manifest['retained_positive_inputs'];old_bad=manifest['retained_rejections']
    old_indices=list(range(old_count))+list(range(len(cases),len(cases)+old_bad))
    old_set=set(old_indices)
    new_indices=[i for i in range(len(programs)) if i not in old_set]
    assert len(programs)==2754 and len(old_indices)==2503 and len(new_indices)==251
    old_input=hashlib.sha256(struct.pack('<I',len(old_indices)));projected=hashlib.sha256(struct.pack('<I',len(old_indices)))
    old_output=hashlib.sha256();input_stride=L['INPUT_WORDS']*4;output_stride=L['OUTPUT_WORDS']*4
    prior_indices=list(range(old_count))+list(range(manifest['prior_positive_inputs'],manifest['prior_positive_inputs']+old_bad))
    with (args.prior_directory/'input.bin').open('rb') as f,(args.prior_directory/'readback.bin').open('rb') as g:
        assert struct.unpack('<I',f.read(4))[0]==manifest['prior_total_inputs']
        for current,index in zip(old_indices,prior_indices):
            packed=pack_programs([programs[current]])[4:]
            f.seek(4+index*input_stride);assert f.read(input_stride)==packed,('old input changed',current)
            old_input.update(packed)
            projected.update(struct.pack('<I',0x5045566D));projected.update(packed[4:])
            g.seek(index*output_stride);block=g.read(output_stride);assert len(block)==output_stride;old_output.update(block)
    assert projected.hexdigest()==manifest['retained_input_abi6d_sha256']
    assert old_output.hexdigest()==manifest['retained_output_sha256']
    selected=[programs[i] for i in new_indices]
    component=module('incremental_component','research/verify-target-states.py')
    component_cases=json.loads((ROOT/'tests/fixtures/portable-target-states.json').read_text())['cases']
    from portable_target_state_validation import rejection_programs
    positives=[verifier.compile_case(c) for c in component_cases]
    bad,_=rejection_programs(component_cases,verifier.compile_case)
    assert [p[0] for p in selected]==[p[0] for p in positives+bad]
    if args.preflight_only:
        print('Preflight only:old2503 saved bytes/source match;new251 compile identically to shared component;no GPU executed')
        return
    argv=sys.argv;sys.argv=[sys.argv[0],'--backend','cuda']
    try:component.main()
    finally:sys.argv=argv
    current=json.loads((ROOT/'research/portable-target-states-cuda.json').read_text())
    assert current['passed'] and current['raw_rejections_verified']
    assert current['source_sha256']==manifest['source_sha256']
    assert current['input_sha256']==programs_sha(selected)
    evidence=dict(passed=True,source_commit=source,verification_mode='incremental',
        logical_total_inputs=len(programs),current_source_actual_gpu_inputs=len(selected),
        source_identical_saved_inputs=len(old_indices),prior_artifact_commit=manifest['prior_artifact_commit'],
        prior_full_input_sha256=manifest['input_sha256'],prior_full_output_sha256=manifest['output_sha256'],
        retained_input_sha256=old_input.hexdigest(),retained_input_abi6d_sha256=projected.hexdigest(),
        retained_output_sha256=old_output.hexdigest(),component_input_sha256=current['input_sha256'],
        component_output_sha256=current['output_sha256'],source_sha256=current['source_sha256'],
        current_full_input_sha256=programs_sha(programs),
        old_indices=old_indices,new_indices=new_indices,old_positive_count=old_count,old_rejection_count=old_bad,
        compute_worktree_clean=True,no_output_normalization=True,old_gpu_reexecuted=False,
        prior_directory=str(args.prior_directory),component_capture=current['captured'],
        driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (ROOT/'research/portable-target-states-incremental-cuda-parity.json').write_text(json.dumps(evidence,indent=2)+'\n')
    print('Current251 GPU inputs verified;old2503 saved CUDA inputs/outputs and all GPU source bytes match exactly')


if __name__=='__main__':main()
