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
    if HELPER not in out:
        if out.get(SOURCE) == row['after_sha256']:
            raise ValueError('Quantity visited helper absent from source closure')
        return out
    source = (root/SOURCE).read_bytes().decode('utf-8')
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
