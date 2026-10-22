"""Allow only six noinline attributes; preserve every original file token."""
import hashlib,json,re
from pathlib import Path
from portable_weapon_phase_contract import tokens


def verify(root,*,sources=None):
    root=Path(root);fixture=json.loads((root/'tests/fixtures/portable-query-boundaries.json').read_text());names=[]
    for row in fixture['files']:
        source=(sources or {}).get(row['path'],(root/row['path']).read_text())
        for name in row['functions']:
            pattern=r'(?m)^\[noinline\]\n(?=(?:bool|uint|uint64_t) '+re.escape(name)+r'\()'
            source,count=re.subn(pattern,'',source)
            assert count==1,'Query boundary missing or duplicated: '+name
            names.append(name)
        actual=tokens(source)
        assert len(actual)==row['token_count'] and hashlib.sha256(json.dumps(actual,separators=(',',':')).encode()).hexdigest()==row['token_sha256'],'Original query statements/signatures/macros changed: '+row['path']
    assert len(names)==6 and len(set(names))==6
    return dict(verified=True,baseline_commit=fixture['baseline_commit'],functions=names,files=len(fixture['files']),original_file_tokens_preserved=True,gpu_calls=0,scope='Only six noinline attributes; no runtime or compiler memory claim')
