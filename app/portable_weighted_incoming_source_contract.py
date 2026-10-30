"""Exact historical source inverse, not generated-code normalization or a seal."""
import hashlib,json,re
from pathlib import Path
LEDGER_SHA256='93afb12ae4b67224a4cfe099ccf64bead769c52229d85ddfe0b45bfbc282f2f6'
PRODUCT_LEDGER_SHA256='9187d38559f8e40c2735afb95892f8cba4174b8a1ccf01b0d9d4bb0873894d38'

def product_sources(root):
    """Exact inverse of the reviewed product family before legacy audit layers.

    Preserve every old fixture. This proves an explicit historical preimage,
    never numerical equivalence of current product code to the legacy program.
    """
    root=Path(root);path=root/'tests/fixtures/portable-product-source-delta.json'
    if not path.exists():return {}
    raw=path.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=PRODUCT_LEDGER_SHA256:raise ValueError('Product source history ledger changed')
    data=json.loads(raw)
    if (data['schema']!=1 or data['baseline_commit']!='168f1bbf65957a85ba48a58699e585f74aa5ad91'
            or data['normalizer_changed'] is not False or data['current_product_equivalence_claim'] is not False):
        raise ValueError('Product source history scope changed')
    for name,digest in data['added_sources'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Unreviewed product dependency: '+name)
    projected={}
    for name,row in data['files'].items():
        text=(root/name).read_text();digest=hashlib.sha256(text.encode()).hexdigest()
        # Reviewed product tap/hold corrections reuse existing native consumers.
        # Restore the exact prior source before applying the unchanged ledger;
        # this is historical recovery, never a current numerical equivalence.
        if name=='gpu/world_charge_control_runtime.slang' and digest=='dd297a8a32a1989f8a744abb75a991e4952f1a5a214e01cb0b8e4a125738ca5f':
            corrected='#if defined(PORTABLE_COORDINATE_ORIGINAL_FORCED_RELOAD) || defined(PORTABLE_PRODUCT_OUTLINED_HELPERS)'
            if text.count(corrected)!=2:raise ValueError('Product charge history spans differ')
            text=text.replace(corrected,'#ifdef PORTABLE_COORDINATE_ORIGINAL_FORCED_RELOAD')
            digest=hashlib.sha256(text.encode()).hexdigest()
            if digest!='aa8df45901d9d3a7e19d6af41bbd6a0a1721594156ea56c4dd1f47cde900c33d':raise ValueError('Product charge history preimage differs')
        if digest==row['baseline_sha256']:
            projected[name]=text;continue
        if digest!=row['current_sha256']:raise ValueError('Unreviewed product source: '+name)
        boundary=len(text)
        for hunk in reversed(row['hunks']):
            start,end=hunk['start'],hunk['end']
            if not 0<=start<=end<=boundary or text[start:end]!=hunk['current']:
                raise ValueError('Product source inverse spans differ: '+name)
            text=text[:start]+hunk['baseline']+text[end:];boundary=start
        if hashlib.sha256(text.encode()).hexdigest()!=row['baseline_sha256']:raise ValueError('Product source preimage differs: '+name)
        projected[name]=text
    return projected

def project_sources(root):
    root=Path(root);raw=(root/'tests/fixtures/portable-weighted-incoming-source-delta.json').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=LEDGER_SHA256:raise ValueError('Weighted source inverse ledger changed')
    data=json.loads(raw)
    if data['schema']!=1 or data['normalizer_changed'] is not False or data['baseline_commit']!='e93182fb61ed6fce5cb7d02e13e1aa5ac59ec840':raise ValueError('Weighted source baseline changed')
    for name,digest in data['added_sources'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('Unreviewed weighted dependency: '+name)
    projected=product_sources(root)
    for name,row in data['files'].items():
        text=projected.get(name,(root/name).read_text())
        if hashlib.sha256(text.encode()).hexdigest()!=row['after_sha256']:raise ValueError('Unreviewed weighted source: '+name)
        for hunk in reversed(row['hunks']):
            if text.count(hunk['after'])!=1:raise ValueError('Ambiguous weighted source inverse: '+name)
            text=text.replace(hunk['after'],hunk['before'],1)
        if hashlib.sha256(text.encode()).hexdigest()!=row['before_sha256']:raise ValueError('Weighted source preimage differs: '+name)
        projected[name]=text
    return projected
def projected_hashes(root,source,sources):
    root=Path(root).resolve();found={}
    def visit(path):
        name=path.relative_to(root).as_posix()
        if name in found:return
        raw=sources[name].encode() if name in sources else path.read_bytes();found[name]=hashlib.sha256(raw).hexdigest()
        for inc in re.findall(rb'^\s*#include\s+"([^"]+)"',raw,re.M):visit((path.parent/inc.decode()).resolve())
    visit(root/source);return found
def historical_hashes(root,source):return projected_hashes(root,source,project_sources(root))
