"""Exact group integration inverse for historical audits, never normalization."""
import hashlib,json
from pathlib import Path

def project_sources(root,sources=None):
    from portable_coordinate_mixed_source_contract import project_sources as project_mixed
    root=Path(root);sources=project_mixed(root,sources);data=json.loads((root/'tests/fixtures/portable-coordinate-group-source-delta.json').read_text())
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed coordinate group source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];sources[name]=row['baseline']
    for name,h in data['added_sources'].items():assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==h,'Unreviewed coordinate group addition: '+name
    return sources

def project_backend_source(root,source=None):
    root=Path(root);row=json.loads((root/'tests/fixtures/portable-coordinate-group-source-delta.json').read_text())['transport'];
    from portable_coordinate_mixed_source_contract import project_backend_source as project_mixed
    current=project_mixed(root,source)
    if current!=row['current'] or hashlib.sha256(current.encode()).hexdigest()!=row['current_sha256']:raise ValueError('Unreviewed coordinate group transport')
    assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256'];return row['baseline']


def historical_source_hashes(root,source,projected):
    """Traverse the exact restored include graph using the primary collector.

    New snippets are not filtered from a current closure. They disappear only
    if the reviewed baseline no longer includes them. Current package admission
    and compile-cache identities continue to hash the real current graph.
    """
    import tempfile
    from portable_slang_generation import source_hashes
    root=Path(root).resolve();project_sources(root)
    with tempfile.TemporaryDirectory() as folder:
        stage=Path(folder).resolve()
        for path in (root/'gpu').glob('*.slang'):
            name=path.relative_to(root).as_posix();to=stage/name;to.parent.mkdir(parents=True,exist_ok=True)
            to.write_bytes(projected[name].encode() if name in projected else path.read_bytes())
        return source_hashes(stage,source)
