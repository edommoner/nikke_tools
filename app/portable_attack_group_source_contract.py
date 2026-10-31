"""Exact reviewed inverse for historical source audits, never GPU normalization."""
import hashlib,json,re
from pathlib import Path

def project_sources(root,sources=None):
    from portable_arena_composed_source_contract import project_sources as project_composition
    root=Path(root);sources=project_composition(root,sources)
    data=json.loads((root/'tests/fixtures/portable-attack-group-source-delta.json').read_text())
    for name,digest in data['added_sources'].items():
        assert hashlib.sha256(sources.get(name,(root/name).read_text()).encode()).hexdigest()==digest,'Unreviewed added attack-group source: '+name
    for name,row in data['sources'].items():
        current=sources.get(name,(root/name).read_text())
        assert current==row['current'] and hashlib.sha256(current.encode()).hexdigest()==row['current_sha256'],'Unreviewed attack-group source: '+name
        assert hashlib.sha256(row['baseline'].encode()).hexdigest()==row['baseline_sha256']
        sources[name]=row['baseline']
    return sources

def retained_source_hashes(root,source):
    # Rebuild the exact old include closure. Removing a reviewed conditional
    # include must also remove its newly introduced dependency from this old
    # audit only; runtime source_hashes and the strict normalizer stay intact.
    root=Path(root).resolve();projected=project_sources(root);found={}
    def visit(path):
        key=path.relative_to(root).as_posix()
        if key in found:return
        text=projected.get(key,path.read_text())
        if key=='gpu/full_burst_landing_runtime.slang' and key not in projected:
            from portable_coordinate_full_burst_source_contract import project_file
            text=project_file(root,key,text)
        found[key]=hashlib.sha256(text.encode()).hexdigest()
        for include in re.findall(r'^\s*#include\s+"([^"]+)"',text,re.M):visit((path.parent/include).resolve())
    visit(root/source)
    # This API reconstructs historical closures. Apply the existing exact
    # membership-storage inverse too; current runtime/codegen hashes are kept
    # by portable_slang_generation.source_hashes and never use this path.
    from portable_quantity_visited_source_contract import historical_hashes
    return historical_hashes(root,found)
