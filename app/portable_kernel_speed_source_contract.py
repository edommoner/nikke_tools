"""Exact Unit 7 inverse for historical source audits; no GPU parity claim."""
import hashlib
import json
from pathlib import Path

LEDGER_SHA256='cadf759b31876502e1a50c06c024c894946c7b0f7493e61343c325e687f5dbc8'
AFTER_SHA256={'gpu/carrier_runtime.slang': 'c598263a801671e1a43a914e6325d610d26f3cef00f304d91fb0fc6465c6fe56', 'gpu/combat_runtime.slang': 'd0ef2419f8db2d5cee4ca3f6a74781c8abb90204c89ea903f2092344b28df518', 'gpu/damage_runtime.slang': '5a72fc2dd2c6673a7088f997b15ecea9f38c3609faffe02476d0ba168f3972d4', 'gpu/definition_runtime.slang': '8225327f8d1da45f81463358b17f3ccab76bd2a46a4996c5dbb59ad5b5a069a5', 'gpu/event_runtime.slang': '5061d96ca32bfd68fdc0c07889c427c3db01a907b0cd319541b163b2af6f6c5f', 'gpu/program_phases.slang': 'b3789ceb8626ab3f49662f02fe08cc63def59a47529c9c5764dd84e84f708478', 'gpu/quantity_runtime.slang': 'ccad6ba58651f262983a8c9dc44523d7d135ffac987aa6a013e9400f988b9f28', 'gpu/runtime_init.slang': '4d2b8120485c92cb093fdc67d1be8429e25c08b822b458aff1cbc3a5bfeb464a', 'gpu/stack_runtime.slang': '05201356d7502acde5a065b7662d8e073a2aa0eb8a6bf32c956457a81a37e39a', 'app/portable_cpu_tests.py': '56c9dea346653762f43814b4782cac52ca1a3e8a3dd2152418d0e25e59af8f52', 'app/portable_detail.py': 'bd99bc53d03e316a3873e12fde2de009b724dc13270fdca5c90f23ff0d34965f'}


def ledger(root):
    raw=(Path(root)/'tests/fixtures/portable-kernel-speed-source-delta.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:raise ValueError('Unit 7 source ledger changed')
    data=json.loads(raw)
    if (data.get('schema')!='kernel-speed-source-history-v1' or data.get('baseline_commit')!='61e79b66da3e7cc8984a92428646ff3474e5d53a'
        or data.get('normalizer_changed') is not False or data.get('current_gpu_equivalence_claim') is not False):
        raise ValueError('Unit 7 source history scope changed')
    return data


def historical_bytes(root,name,raw):
    row=ledger(root)['files'][name];digest=hashlib.sha256(raw).hexdigest()
    if digest==row['before_sha256']:return raw
    if digest!=row['after_sha256']:raise ValueError('Unreviewed Unit 7 source: '+name)
    text=raw.decode();boundary=len(text)
    for hunk in reversed(row['hunks']):
        start,end=hunk['start'],hunk['end']
        if not 0<=start<=end<=boundary or text[start:end]!=hunk['after']:raise ValueError('Unit 7 inverse span differs: '+name)
        text=text[:start]+hunk['before']+text[end:];boundary=start
    raw=text.encode()
    if hashlib.sha256(raw).hexdigest()!=row['before_sha256']:raise ValueError('Unit 7 historical preimage differs: '+name)
    return raw


def reviewed_bytes(root,name,raw):
    if name in AFTER_SHA256 and hashlib.sha256(raw).hexdigest()==AFTER_SHA256[name]:return historical_bytes(root,name,raw)
    return raw


def preimages(root):
    out={}
    data=ledger(root)
    for name,digest in AFTER_SHA256.items():
        path=Path(root)/name
        if path.is_file():
            raw=path.read_bytes()
            current=hashlib.sha256(raw).hexdigest()
            if current in (digest,data['files'][name]['before_sha256']):out[name]=historical_bytes(root,name,raw).decode()
    return out
