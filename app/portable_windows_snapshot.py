"""CPU-only diagnostic of the same fail-closed Windows process observer."""
import json,re,subprocess,time
from pathlib import Path


def check(workspace,validation_root,output,*,reader=None):
    workspace,validation_root,output=map(Path,(workspace,validation_root,output))
    if not all(p.is_absolute() for p in (workspace,validation_root,output)):
        raise ValueError('Absolute snapshot paths required')
    workspace,validation_root,output=(p.resolve() for p in (workspace,validation_root,output))
    if not workspace.is_dir() or not validation_root.is_dir():raise ValueError('Existing original and validation directories required')
    if workspace.is_relative_to(validation_root) or validation_root.is_relative_to(workspace):raise ValueError('Separate original and validation directories required')
    if not output.is_relative_to(validation_root) or not output.parent.is_dir():raise ValueError('Snapshot report must be inside existing validation directory')
    if output.exists() or output.is_symlink():raise FileExistsError(output)
    if reader is None:
        from windows_validation_observer import capture_snapshot
        reader=capture_snapshot
    started=time.perf_counter()
    result=dict(schema='windows-snapshot-check-v1',snapshot_verified=False,gpu_calls=0,
                calculation_verified=False,preservation_verified=None,
                scope='One read-only process/listener snapshot; not a before/after preservation or CUDA calculation proof')
    # Reserve the report first: never repeat a query because a report already exists.
    with output.open('x',encoding='utf-8') as stream:
        try:
            result['snapshot']=reader(workspace,validation_root)
            result['snapshot_verified']=True
        except Exception as error:
            message=str(error)
            safe=None
            if isinstance(error,RuntimeError) and (message in ('Windows process capture requires Windows','Invalid process snapshot; no command lines retained','Windows process snapshot unavailable; no command lines retained') or re.fullmatch(r'Windows process snapshot unavailable \(exit=(?:-?\d+|None), stage=(?:setup|processes|listeners|serialize|unknown), category=(?:-?\d+|None), hresult=(?:-?\d+|None)\); no command lines retained',message)):
                safe=message
            result['error']=dict(type=type(error).__name__,message=safe)
            if isinstance(error,subprocess.TimeoutExpired):result['error']['timeout_seconds']=error.timeout
        result['elapsed_seconds']=time.perf_counter()-started
        json.dump(result,stream,indent=2);stream.write('\n')
    return result
