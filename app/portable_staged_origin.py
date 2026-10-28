"""Freeze a completely revalidated old preflight without replaying its battle.

This is evidence preparation, not a recovery admission or an execution permit.
The old package's own CLI remains the authority for its registry and receipts.
"""
import json,os,stat,subprocess,sys
from pathlib import Path

SCHEMA='staged-origin-check-v1'


def evidence_roots(cli,root,outer,admission):
    """Only the explicit admission closure, never the original workspace tree."""
    roots={Path(root).resolve(),Path(outer).resolve()}
    tx=Path(admission['transaction']).resolve();seen=set()
    while tx not in seen:
        seen.add(tx);c=cli.load(tx/'transaction.json')
        if c.get('transaction')!=str(tx):raise ValueError('Origin transaction location changed')
        owner=Path(c['package_root']).resolve();m=cli.load(owner/'gpu-package.json')
        if m.get('package_id')!=c.get('package_id'):raise ValueError('Origin transaction owner changed')
        roots.update((tx,owner))
        parent=c.get('resume_parent')
        if parent is None:break
        tx=Path(parent['transaction']).resolve()
    else:raise ValueError('Origin continuation cycle')
    for stage in admission['stage_envelopes']:
        proof=Path(stage['capture']).resolve()
        if proof.name!='proof':raise ValueError('Origin stage lacks explicit bounded proof directory')
        plan=cli.load(proof.parent/'recipe.json')
        if Path(plan['proof_capture']).resolve()!=proof or plan.get('original_workspace')==str(proof.parent):raise ValueError('Origin stage location changed')
        roots.add(proof.parent)
    failed=admission.get('original_timeout')
    if failed is not None:
        proof=Path(failed['capture']).resolve()
        if proof.name!='proof':raise ValueError('Origin timeout lacks bounded proof directory')
        plan=cli.load(proof.parent/'recipe.json')
        if Path(plan['proof_capture']).resolve()!=proof:raise ValueError('Origin timeout location changed')
        roots.add(proof.parent)
    # Drop descendants already included by an explicit enclosing evidence root.
    return sorted((p for p in roots if not any(q in p.parents for q in roots)),key=str)


def inventory(cli,roots):
    """Freeze names too: newly added files and symbolic links fail rechecks."""
    result=[]
    def walk_error(error):raise error
    def real_entry(path):
        info=path.lstat()
        if (getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0)
            or not (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode))):
            raise ValueError('Origin evidence contains a link or special file: '+str(path))
    for root in roots:
        root=Path(root)
        if not root.is_dir() or root.is_symlink():raise ValueError('Origin evidence root must be a real directory')
        real_entry(root)
        names=[]
        for directory,dirs,files in os.walk(root,followlinks=False,onerror=walk_error):
            for name in (*dirs,*files):
                real_entry(Path(directory)/name)
            names.extend((Path(directory)/name).relative_to(root).as_posix() for name in files)
        result.append(dict(root=str(root),files=cli.file_records(root,names)))
    return result


def validate_admission(cli,root,outer,admission,expected_package_id):
    """Bind the old complete receipt to this exact failed execution and host."""
    from portable_staged_preflight import host
    m=cli.load(Path(root)/'gpu-package.json');tx=Path(admission['transaction']).resolve()
    c=cli.load(tx/'transaction.json')
    if (m.get('package_id')!=expected_package_id or admission.get('package_id')!=expected_package_id
        or admission.get('schema')!='staged-native-preflight-v1' or admission.get('host')!=host(cli)
        or admission.get('transaction_sha256')!=cli.sha((tx/'transaction.json').read_bytes())
        or admission.get('transaction_nonce')!=c.get('nonce') or c.get('package_root')!=str(Path(root).resolve())
        or c.get('gpu_capture')!=str((Path(outer)/'proof').resolve()) or c.get('backend')!='cuda'
        or admission.get('all_native_preflight_verified') is not True or admission.get('calculation_verified') is not False
        or type(admission.get('gpu_calls')) is not int or admission['gpu_calls']!=0
        or type(admission.get('input_count')) is not int or admission['input_count']!=len(m['golden']['entries'])
        or type(admission.get('native_cases')) is not int or admission['native_cases']!=len(c['native_indices'])
        or admission.get('input')!=c.get('input')):
        raise ValueError('Origin admission identity/count/host mismatch')


def readmit(root,transaction,gpu_capture,output):
    """Separate interpreter prevents current modules/registry replacing old ones.

    On Windows call from the packet wrapper's fresh Job stage; all descendant
    verifiers inherit that Job. No compiler, native oracle or GPU command runs.
    """
    env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
    command=[sys.executable,'-B',str(Path(root)/'scripts/nikke_gpu.py'),'staged-preflight-check',
        '--backend','cuda','--transaction',str(transaction),'--gpu-capture',str(gpu_capture),'--out',str(output)]
    completed=subprocess.run(command,cwd=root,env=env,capture_output=True,text=True,timeout=120,check=True)
    # Preserve the real old-owner stdout, including its compact admission counts.
    return completed.stdout,completed.stderr


def check(cli,package_root,capture,output,expected_package_id):
    from portable_staged_preflight import outside,exclusive
    from portable_staged_failure import check as failure_check
    root=Path(package_root).resolve();outer=Path(capture).resolve();output=Path(output).resolve()
    saved=cli.load(outer/'proof/staged-preflight.json')
    roots=evidence_roots(cli,root,outer,saved)
    outside(output,roots);output.mkdir(parents=True,exist_ok=False)
    report=dict(schema=SCHEMA,mode='saved-staged-origin-audit',passed=False,package_id=expected_package_id,
        execution_permitted=False,recovery_admission_verified=False,linked_artifact_revalidated=False,
        native_admission_revalidated=False,host_revalidated=False,calculation_verified=False,
        claims_modified=False,native_values_reused=False,gpu_calls=0,compiler_calls=0,native_calls=0)
    try:
        failure=failure_check(cli,root,outer,output/'failure-audit.json',expected_package_id)
        before=inventory(cli,roots)
        stdout,stderr=readmit(root,saved['transaction'],outer/'proof',output/'admission.json')
        exclusive(output/'owner-output.json',dict(stdout=stdout,stderr=stderr))
        actual=cli.load(output/'admission.json')
        if actual!=saved:raise ValueError('Original own-CLI admission differs from failed execution receipt')
        validate_admission(cli,root,outer,actual,expected_package_id)
        if inventory(cli,roots)!=before:raise ValueError('Original evidence changed during admission audit')
        closure=dict(schema='staged-origin-inventory-v1',package_id=expected_package_id,
            source_package=str(root),source_capture=str(outer),evidence=before,
            admission_sha256=cli.sha((output/'admission.json').read_bytes()))
        exclusive(output/'origin-inventory.json',closure)
        report.update(passed=True,native_admission_revalidated=True,host_revalidated=True,
            input_count=actual['input_count'],native_cases=actual['native_cases'],
            process_preservation_verified=failure['process_preservation_verified'],
            environment_preservation_verified=failure['environment_preservation_verified'],
            evidence_roots=len(before),evidence_files=sum(len(r['files']) for r in before),
            inventory_sha256=cli.sha((output/'origin-inventory.json').read_bytes()),
            scope='Complete old preflight revalidated without numerical replay. No recovery admission, CUBIN/cache validation or execution permission.')
    except BaseException as error:
        report['error']=type(error).__name__+': '+str(error);raise
    finally:exclusive(output/'result.json',report)
    return report
