"""Opt-in exact-byte NVRTC artifact cache. No generated-source normalization."""
import base64
import hashlib
import json
import os
import re
from pathlib import Path
import tempfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def quoted_headers(source):
    """Slang emits an absolute prelude include; preserve its actual contents too."""
    found={}
    def visit(raw, parent):
        for name in re.findall(rb'^\s*#\s*include\s*"([^"\n]+)"',raw,re.M):
            path=Path(name.decode())
            if not path.is_absolute():path=parent/path
            path=path.resolve()
            if path in found:continue
            data=path.read_bytes();found[path]=data;visit(data,path.parent)
    visit(source,Path.cwd())
    return list(found)


def get_or_compile(source, options, compiler_files, compile_fn, directory=None, *, header_files=(), artifact_kind='ptx'):
    if artifact_kind not in ('ptx','cubin'):raise ValueError('Unsupported CUDA artifact kind')
    compiler_files=list(map(Path,compiler_files));header_files=list(map(Path,header_files))
    identity = dict(schema=1, artifact=artifact_kind, source_sha256=sha(source),
                    options=list(options),
                    headers={str(p.resolve()):sha(p.read_bytes()) for p in sorted(map(Path,header_files))},
                    compiler_files={p.name:sha(p.read_bytes()) for p in sorted(map(Path,compiler_files))})
    key = sha(json.dumps(identity,sort_keys=True,separators=(',',':')).encode())
    path = Path(directory)/f'{key}.json' if directory is not None else None
    if path and not identity['compiler_files']:
        raise ValueError('CUDA cache requires compiler binary identities')
    hit = bool(path and path.exists())
    if hit:
        value = json.loads(path.read_bytes())
        if value['identity'] != identity: raise ValueError('CUDA compile cache identity mismatch')
        artifact = base64.b64decode(value['artifact_base64'],validate=True)
        if sha(artifact) != value['artifact_sha256'] or len(artifact)!=value['artifact_bytes']:
            raise ValueError('CUDA compile cache artifact integrity failure')
    else:
        artifact = compile_fn()
        if {str(p.resolve()):sha(p.read_bytes()) for p in sorted(map(Path,header_files))} != identity['headers']:
            raise ValueError('CUDA headers changed during compilation')
        if {p.name:sha(p.read_bytes()) for p in sorted(map(Path,compiler_files))} != identity['compiler_files']:
            raise ValueError('CUDA compiler changed during compilation')
        if not isinstance(artifact,bytes) or not artifact: raise ValueError('Empty/invalid compiler artifact')
        if path:
            path.parent.mkdir(parents=True,exist_ok=True)
            value = dict(identity=identity, artifact_base64=base64.b64encode(artifact).decode(),
                         artifact_sha256=sha(artifact),artifact_bytes=len(artifact))
            with tempfile.NamedTemporaryFile(dir=path.parent,delete=False) as stream:
                temporary=Path(stream.name)
                stream.write(json.dumps(value,sort_keys=True).encode());stream.flush();os.fsync(stream.fileno())
            try: temporary.replace(path)
            finally: temporary.unlink(missing_ok=True)
    return artifact,dict(enabled=path is not None,hit=hit,key=key,identity=identity,
                         artifact_sha256=sha(artifact),artifact_bytes=len(artifact))
