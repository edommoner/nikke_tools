"""Immutable, hash-pinned header bytes omitted from an older admission trace.

The base certificate/receipt is never rewritten. This supplies dependency
bytes only, with no native values, compiler call, execution claim or GPU.
"""
import copy,json
from pathlib import Path
from portable_admission_snapshot import Snapshot,INVENTORY,binding,digest,freeze,hex_string
from portable_staged_preflight import exclusive

SCHEMA='prepared-header-materials-v1'


class Materials:
    def __init__(self,descriptor,expected_binding,base_sha,cert_sha,expected_headers):
        if type(descriptor) is not dict or set(descriptor)!={'snapshot','sha256','manifest_sha256'} or not hex_string(descriptor['manifest_sha256'],64):raise ValueError('Exact external header materials descriptor required')
        self.descriptor=copy.deepcopy(descriptor);self.expected=copy.deepcopy(expected_headers)
        self.archive=Snapshot(descriptor['snapshot'],descriptor['sha256'],expected_binding=expected_binding)
        try:
            meta=json.loads(self.archive.read_blob('blobs/'+descriptor['manifest_sha256']))
            if (meta['schema']!=SCHEMA or meta['binding']!=expected_binding
                or meta['base_snapshot_sha256']!=base_sha or meta['base_certificate_sha256']!=cert_sha
                or meta['material_bytes_verified'] is not True or meta['calculation_verified'] is not False
                or type(meta['gpu_calls']) is not int or meta['gpu_calls']!=0
                or type(meta['headers']) is not dict or set(meta['headers'])!=set(expected_headers)):
                raise ValueError('Header materials base/scope mismatch')
            for name,row in meta['headers'].items():
                if (type(row) is not dict or set(row)!={'bytes','sha256'} or type(row['bytes']) is not int
                    or row['bytes']<0 or row['sha256']!=expected_headers[name]):raise ValueError('Header materials expected identity mismatch')
                raw=self.archive.read_blob('blobs/'+row['sha256'])
                if len(raw)!=row['bytes']:raise ValueError('Header materials byte size mismatch')
            if {r['blob'] for r in self.archive.meta['files']}!={'blobs/'+descriptor['manifest_sha256'],*('blobs/'+s for s in expected_headers.values())}:
                raise ValueError('Unrelated material payload')
            self.meta=meta
        except BaseException:
            self.archive.__exit__(None,None,None);raise
    def read(self,name):
        if name not in self.expected:raise ValueError('Unlisted header material')
        return self.archive.read_blob('blobs/'+self.expected[name])
    def close(self,*error):return self.archive.__exit__(*error)


def create(cli,snapshot,expected_sha256,certificate_sha256,expected_binding,out,*,sources=None):
    """Complete known missing dependencies, then use the ordinary reader again."""
    from portable_admission_handoff import Handoff,origin_key
    out=Path(out).resolve();snapshot=Path(snapshot).resolve();sources={} if sources is None else dict(sources)
    if any(out==p or p in out.parents or out in p.parents for p in (cli.ROOT.resolve(),snapshot.parent)):
        raise ValueError('Header materials output must be separate')
    out.mkdir(parents=True,exist_ok=False)
    collected={}
    class Collector(Handoff):
        def _header_bytes(self,name):
            if origin_key(name) in self._index:return super()._header_bytes(name)
            expected=self._cert['linked_receipt']['identity']['headers'][name]
            path=Path(sources.get(name,name)).resolve();raw=path.read_bytes()
            if digest(raw)!=expected:raise ValueError('Live header does not match the authenticated expected SHA')
            collected[name]=(path,len(raw),expected);return raw
    try:
        with cli.forbid_gpu():
            m=cli.verify_package(cli.ROOT)
            if cli.is_development(m) or cli.compiler_only(m):raise ValueError('Header materialization requires a sealed consumer')
            args=dict(certificate_sha256=certificate_sha256,expected_binding=binding(expected_binding),expected_suite=m['suite'],expected_golden=m['golden'],consumer_package_id=m['package_id'])
            with Collector(cli,snapshot,expected_sha256,**args):pass
            if not collected or not set(sources)<=set(collected):raise ValueError('Only known missing header dependencies may be materialized')
            evidence=out/'evidence';evidence.mkdir()
            meta=dict(schema=SCHEMA,binding=expected_binding,base_snapshot_sha256=expected_sha256,base_certificate_sha256=certificate_sha256,
                headers={name:dict(bytes=size,sha256=sha) for name,(_,size,sha) in collected.items()},material_bytes_verified=True,calculation_verified=False,gpu_calls=0)
            exclusive(evidence/'materials.json',meta);raw=(evidence/'materials.json').read_bytes();metadata_sha=digest(raw)
            rows={str(path):dict(root=str(path.parent),path=path.name,bytes=size,sha256=sha) for path,size,sha in collected.values()}
            rows[str(evidence/'materials.json')]=dict(root=str(evidence),path='materials.json',bytes=len(raw),sha256=metadata_sha)
            result=freeze(dict(schema=INVENTORY,binding=expected_binding,files=list(rows.values())),out/'header-materials.zip')
            descriptor=dict(snapshot=str(out/'header-materials.zip'),sha256=result['snapshot_sha256'],manifest_sha256=metadata_sha)
            with Handoff(cli,snapshot,expected_sha256,header_materials=descriptor,**args) as reader:checked=reader.summary()
            report=dict(schema=SCHEMA,descriptor=descriptor,headers=len(collected),base_snapshot_sha256=expected_sha256,base_certificate_sha256=certificate_sha256,
                material_bytes_verified=True,complete_handoff_bytes_verified=checked['handoff_bytes_verified'],preparation_reexecuted=False,
                execution_admitted=False,calculation_verified=False,gpu_calls=0)
            exclusive(out/'descriptor.json',descriptor);exclusive(out/'result.json',report);return report
    except BaseException as error:
        exclusive(out/'failure.json',dict(error=type(error).__name__+': '+str(error),material_bytes_verified=False,calculation_verified=False,gpu_calls=0));raise
