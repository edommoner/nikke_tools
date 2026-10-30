"""Exact registration inverse for earlier audits, never a GPU normalizer."""
import hashlib,json
from pathlib import Path
BEFORE_BACKEND_SHA256='b5234e00159b5d747c95c24578a6630c495f8174bac5e7a84ae97dc4a7fe05a9'
BEFORE_AREA_SHA256='914fa3c781b865af2d7059a7e055fa32045e0fe7882f94731d940c4994c3a1e2'
AFTER_BACKEND_SHA256='a435f15cf96e980e3471eb4cb29bcb08b683b0765117c1faf31f04cc060d5352'
AFTER_AREA_SHA256='7de8a80bcf3686e1b266e644e591a08094b70991ec1bb5eb3948b423586c07a9'

def project_sources(root,sources=None):
    root=Path(root);out=dict(sources or {});later={}
    if (root/'gpu/world_cover_defense_entry.slang').exists():
        from portable_cover_defense_source_contract import project_sources as cover
        later=cover(root);out={**later,**out}
    from portable_recipient_order_observation import check_layout,SOURCE
    check_layout(root)
    data=json.loads((root/'tests/fixtures/portable-recipient-order-observation-source-delta.json').read_text(encoding='utf-8'))
    if (set(data)!={'schema','normalizer_changed','baseline_commit','files','added_sources'} or
        data['schema']!=1 or data['normalizer_changed'] is not False or
        data['baseline_commit']!='b4f43db13c7d94d8b272b75f046d43f502602033' or
        set(data['files'])!={'app/portable_backend.py','gpu/world_coordinate_area_entry.slang'} or set(data['added_sources'])!={SOURCE}):
        raise ValueError('Unreviewed recipient-order registration ledger')
    digest=lambda text:hashlib.sha256(text.encode()).hexdigest()
    if digest(out.get(SOURCE,(root/SOURCE).read_text(encoding='utf-8')))!=data['added_sources'][SOURCE]:
        raise ValueError('Recipient-order entry dependency changed')
    anchors={'app/portable_backend.py':(BEFORE_BACKEND_SHA256,AFTER_BACKEND_SHA256),'gpu/world_coordinate_area_entry.slang':(BEFORE_AREA_SHA256,AFTER_AREA_SHA256)}
    for name,(anchor,after_anchor) in anchors.items():
        row=data['files'][name]
        if (set(row)!={'before_sha256','after_sha256','hunks'} or row['before_sha256']!=anchor or
            row['after_sha256']!=after_anchor or len(row['hunks'])!=1 or set(row['hunks'][0])!={'before','after'}):
            raise ValueError('Recipient-order source anchor changed')
        current=later.get(name,(root/name).read_text(encoding='utf-8'))
        if digest(current)!=row['after_sha256']:raise ValueError('Recipient-order registered source changed')
        before=current
        for hunk in reversed(row['hunks']):
            if before.count(hunk['after'])!=1:raise ValueError('Ambiguous recipient-order registration inverse')
            before=before.replace(hunk['after'],hunk['before'],1)
        if digest(before)!=anchor:raise ValueError('Recipient-order registration preimage changed')
        value=out.get(name,current)
        if value==current:out[name]=before
        elif value==before:out[name]=value
        else:
            # Earlier callers may already hold one of these strictly checked
            # preimages; their own layer still verifies its complete contents.
            allowed=set()
            for filename in ('portable-moving-many-source-delta.json','portable-moving-typed-source-delta.json','portable-enemy-movement-source-delta.json'):
                record=json.loads((root/'tests/fixtures'/filename).read_text())['files'].get(name,{})
                allowed.update(record.get(key) for key in ('before_sha256','after_sha256'))
            if digest(value) not in allowed:raise ValueError('Unreviewed projected recipient-order source')
    return out
