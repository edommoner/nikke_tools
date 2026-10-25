"""Reuse one deterministic migration check inside a fresh audit, never oracles.

The complete battle comparison still runs fresh. Before a repeated metadata
check, rehash both frozen payloads and all small receipt anchors.
"""
import contextlib,copy,hashlib,json
from pathlib import Path
from unittest.mock import patch

@contextlib.contextmanager
def reuse(module,capture):
    stats=dict(fresh_checks=0,reused_checks=0,native_comparison_reuse=False)
    capture=Path(capture);origin_path=capture/'replay.json'
    if not origin_path.is_file() or not hasattr(module,'verify_reference_migration'):
        yield stats;return
    origin=json.loads(origin_path.read_text())
    if origin.get('reference_migration')!='coordinate-healing-routed-adds-v1':
        yield stats;return
    source=Path(origin['source_package']);root=Path(module.ROOT)
    paths=[root/'gpu-package.json',source/'gpu-package.json',origin_path,capture/'reference-migration.json',capture/'artifacts.json']
    def anchors():return [hashlib.sha256(p.read_bytes()).hexdigest() for p in paths]
    initial=anchors();original=module.verify_reference_migration;cache=[];inputs=[]
    def unchanged(old,current):
        if anchors()!=initial:raise ValueError('Frozen migration receipt context changed')
        module.check_records(root,current['files']);module.check_records(source,old['files'])
    def checked(name,old,current):
        if name!=origin['reference_migration']:return original(name,old,current)
        key=hashlib.sha256(json.dumps([name,old,current],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if cache:
            if key!=cache[0][0]:raise ValueError('Frozen migration receipt context changed')
            unchanged(old,current)
            stats['reused_checks']+=1;return copy.deepcopy(cache[0][1])
        result=original(name,old,current)
        if anchors()!=initial:raise ValueError('Frozen migration receipt context changed')
        cache.append((key,copy.deepcopy(result),old,current));stats['fresh_checks']+=1;return result
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(module,'verify_reference_migration',checked))
        if hasattr(module,'prepare_entries'):
            from portable_parent_oracles import stamp
            prepare=module.prepare_entries
            stats.update(fresh_input_preparations=0,reused_input_preparations=0)
            def prepared(adapter,manifest):
                key=(str(Path(adapter.__file__).resolve()),stamp(manifest))
                if not inputs:
                    result=prepare(adapter,manifest);inputs.append((key,result,stamp(result)))
                    stats['fresh_input_preparations']+=1;return result
                if key!=inputs[0][0] or stamp(inputs[0][1])!=inputs[0][2]:raise ValueError('Frozen prepared input/domain changed')
                if not cache:raise ValueError('Prepared input reuse requires completed migration validation')
                unchanged(cache[0][2],cache[0][3]);stats['reused_input_preparations']+=1
                return inputs[0][1]
            stack.enter_context(patch.object(module,'prepare_entries',prepared))
        yield stats
