"""Restore the reviewed append audit only for the original extraction proof."""
import hashlib,json
from pathlib import Path


OUTPUT_GUARDS_LEDGER_SHA256='49579c0fe8b2105275ac029c20119def3b6a48668d29ee5732a4278913dac1e3'
OUTPUT_GUARDS_AFTER_SHA256='a3285cc9b372e4bb592fd70fdc18e44b07b6803a2c432eca8a8f0493eae76dac'


def output_guards_preimage(root,source):
    if hashlib.sha256(source.encode()).hexdigest()!=OUTPUT_GUARDS_AFTER_SHA256:return source
    raw=(Path(root)/'tests/fixtures/portable-generation-output-guards-source-delta.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=OUTPUT_GUARDS_LEDGER_SHA256:raise ValueError('Generation output guards ledger changed')
    row=json.loads(raw);boundary=len(source)
    for hunk in reversed(row['hunks']):
        start,end=hunk['start'],hunk['end']
        if not 0<=start<=end<=boundary or source[start:end]!=hunk['after']:raise ValueError('Generation output guards inverse span changed')
        source=source[:start]+hunk['before']+source[end:];boundary=start
    if hashlib.sha256(source.encode()).hexdigest()!=row['before_sha256']:raise ValueError('Generation output guards historical preimage changed')
    return source


def project_generation_source(root,source=None):
    root=Path(root);name='app/portable_slang_generation.py'
    row=json.loads((root/'tests/fixtures/portable-generation-append-audit-delta.json').read_text())
    source=(root/name).read_text() if source is None else source
    from portable_native_backend_source_contract import reviewed_bytes
    source=reviewed_bytes(root,name,source.encode('utf-8')).decode('utf-8')
    source=output_guards_preimage(root,source)
    digest=lambda text:hashlib.sha256(text.encode()).hexdigest()
    if digest(source)!=row['current_sha256']:raise ValueError('Unreviewed generation extraction source')
    for h in reversed(row['hunks']):
        if source.count(h['after'])!=1:raise ValueError('Ambiguous generation extraction inverse')
        source=source.replace(h['after'],h['before'],1)
    if digest(source)!=row['baseline_sha256']:raise ValueError('Generation extraction baseline changed')
    return source
