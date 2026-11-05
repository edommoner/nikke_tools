"""Exact Unit 6 inverse for historical source audits; no GPU parity claim."""
import hashlib
import json
from pathlib import Path

LEDGER_SHA256='0f334fe1196f0ae88057ba279be9ad20f9b7d74aa1cd3f3b7e6a2d86c37c9cdb'
AFTER_SHA256={'app/portable_cpu_tests.py': '509d3c1074c7f8798d2531dffb01559f024bdf995f335cddbe31ff0d6d3b11a7', 'app/portable_product_resource_budget.py': '64936f071c27621a54183add74d4c9e8f47f387fc2027740fcb3132c59dc1370', 'app/portable_product_ordinary_lock.py': 'ffa2c39ae4b39d8d6c44887a65d058fe24632632419b4c0472eac248379545ad', 'app/portable_product_named_carriers.py': '746f635dcf9d688a83c17ad6f35754cdd12398166160c5000c3d4b597897ea68', 'app/portable_backend.py': '426a70aa651a18cee2a93b293a47f6ad40a98d54137a125b1662e2b4a2a4f565', 'gpu/stack_runtime.slang': 'bbfc6ed5a20a57f573afe1c2f35f27553e0950c347f816a43cb5afc9160c6504', 'gpu/world_skill_runtime.slang': '77b0bd85b0adb8dd8b6872b6b5116be4445d421b17395a1ea7b212632b6e5124'}


def ledger(root):
    raw=(Path(root)/'tests/fixtures/portable-optimizer-six-source-delta.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:raise ValueError('Unit 6 source ledger changed')
    data=json.loads(raw)
    if (data.get('schema')!='optimizer-six-source-history-v1' or data.get('baseline_commit')!='708f0076bd72f7f4e993d91af85c65c2b3ecc3d1'
        or data.get('normalizer_changed') is not False or data.get('current_gpu_equivalence_claim') is not False):
        raise ValueError('Unit 6 source history scope changed')
    return data


def historical_bytes(root,name,raw):
    from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes
    raw=cpu_only_bytes(root,name,raw)
    from portable_kernel_speed_source_contract import reviewed_bytes as speed_reviewed_bytes
    raw=speed_reviewed_bytes(root,name,raw)
    row=ledger(root)['files'][name];digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:return raw
    if digest!=row['after_sha256']:raise ValueError('Unreviewed Unit 6 source: '+name)
    text=raw.decode();boundary=len(text)
    for hunk in reversed(row['hunks']):
        start,end=hunk['start'],hunk['end']
        if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Unit 6 inverse span differs: '+name)
        text=text[:start]+hunk['before']+text[end:];boundary=start
    raw=text.encode()
    if hashlib.sha256(raw).hexdigest()!=row['before_sha256']:raise ValueError('Unit 6 historical preimage differs: '+name)
    return raw


def reviewed_bytes(root,name,raw):
    from portable_cpu_only_source_contract import reviewed_bytes as cpu_only_bytes
    raw=cpu_only_bytes(root,name,raw)
    from portable_kernel_speed_source_contract import reviewed_bytes as speed_reviewed_bytes
    raw=speed_reviewed_bytes(root,name,raw)
    if name in AFTER_SHA256 and hashlib.sha256(raw).hexdigest()==AFTER_SHA256[name]:return historical_bytes(root,name,raw)
    return raw


def preimages(root):
    from portable_kernel_speed_source_contract import preimages as speed_preimages
    out=speed_preimages(root)
    data=ledger(root)
    for name,digest in AFTER_SHA256.items():
        path=Path(root)/name
        if path.is_file():
            from portable_cpu_only_source_contract import reviewed_text
            raw=out.get(name,reviewed_text(root,name,path.read_text())).encode()
            current=hashlib.sha256(raw).hexdigest()
            if current in (digest,data['files'][name]['before_sha256']):out[name]=historical_bytes(root,name,raw).decode()
    return out
