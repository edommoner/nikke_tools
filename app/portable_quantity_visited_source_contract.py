"""Exact historical source identity only; never current admission or execution."""
import hashlib
import json
from pathlib import Path

SOURCE = 'gpu/quantity_runtime.slang'
HELPER = 'gpu/quantity_visited.slang'
BEFORE_SHA256 = 'd04e568983cc1be4124d5144239cbde63826f51a05c23ba2c7bbb03a0a809020'

def historical_hashes(root, hashes):
    root = Path(root)
    out = dict(hashes)
    data = json.loads((root/'tests/fixtures/quantity-visited-source-change-v1.json').read_bytes())
    if (data.get('schema') != 'quantity-visited-source-change-v1' or
        data.get('normalizer_changed') is not False or set(data.get('files', {})) != {SOURCE} or
        set(data.get('added_sources', {})) != {HELPER}):
        raise ValueError('Unknown quantity visited historical contract')
    row = data['files'][SOURCE]
    if row['before_sha256'] != BEFORE_SHA256:
        raise ValueError('Quantity visited historical baseline changed')
    if SOURCE not in out and HELPER not in out:return out
    from portable_kernel_speed_source_contract import reviewed_bytes as speed_bytes
    actual=(root/SOURCE).read_bytes()
    reviewed=speed_bytes(root,SOURCE,actual)
    if out.get(SOURCE)==hashlib.sha256(actual).hexdigest() and reviewed!=actual:
        out[SOURCE]=hashlib.sha256(reviewed).hexdigest()
    if HELPER not in out:
        if out.get(SOURCE)==row['after_sha256']:
            raise ValueError('Quantity visited helper absent from source closure')
        return out
    source=reviewed.decode('utf-8')
    digest = lambda value: hashlib.sha256(value).hexdigest()
    if (out.get(SOURCE) != row['after_sha256'] or digest(source.encode()) != row['after_sha256'] or
        out[HELPER] != data['added_sources'][HELPER] or
        digest((root/HELPER).read_bytes()) != data['added_sources'][HELPER]):
        raise ValueError('Unreviewed quantity visited source or helper')
    for hunk in reversed(row['hunks']):
        if not hunk['after'] or source.count(hunk['after']) != 1:
            raise ValueError('Ambiguous quantity visited historical inverse')
        source = source.replace(hunk['after'], hunk['before'], 1)
    if digest(source.encode()) != BEFORE_SHA256:
        raise ValueError('Quantity visited historical inverse differs')
    out[SOURCE] = BEFORE_SHA256
    del out[HELPER]
    return out


def historical_source(root,text):
    """Compose the exact visited-set inverse before traversing an old include graph."""
    raw=(Path(root)/'tests/fixtures/quantity-visited-source-change-v1.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!='21349f0d33f4b38e614b1fddafd4a6c978758903017a64ffb5dc7436d29ec20e':raise ValueError('Quantity visited historical ledger changed')
    data=json.loads(raw);row=data['files'][SOURCE]
    digest=hashlib.sha256(text.encode()).hexdigest()
    if digest==BEFORE_SHA256:return text
    if digest!='c3d6af87a8f858aff680c8f309c2d7950ea478169e8a4c223e66c129e20fd646':raise ValueError('Unreviewed quantity visited historical source')
    if hashlib.sha256((Path(root)/HELPER).read_bytes()).hexdigest()!=data['added_sources'][HELPER]:raise ValueError('Unreviewed quantity visited helper')
    for hunk in reversed(row['hunks']):
        if not hunk['after'] or text.count(hunk['after'])!=1:raise ValueError('Ambiguous quantity visited historical inverse')
        text=text.replace(hunk['after'],hunk['before'],1)
    if hashlib.sha256(text.encode()).hexdigest()!=BEFORE_SHA256:raise ValueError('Quantity visited historical inverse differs')
    return text
