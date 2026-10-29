"""Byte-frozen, content-addressed handoff storage; never GPU admission.

The independent preparation/claim protocol must authenticate expected_sha256.
This module cannot turn a caller-provided inventory into a calculation proof.
"""
import copy,hashlib,json,stat,zipfile
from pathlib import Path,PurePosixPath,PureWindowsPath

SCHEMA='prepared-admission-snapshot-v1'
INVENTORY='prepared-admission-file-inventory-v1'
MAX_FILES=65536
MAX_FILE=256*1024*1024
MAX_TOTAL=1024*1024*1024
MAX_MANIFEST=16*1024*1024
BINDING=('owner_package_id','controller_package_id','transaction_nonce','input_sha256','artifact_sha256','future_capture')


def digest(raw):return hashlib.sha256(raw).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
def hex_string(value,size):return type(value) is str and len(value)==size and all(c in '0123456789abcdef' for c in value)
def absolute_metadata(value):return type(value) is str and (PurePosixPath(value).is_absolute() or PureWindowsPath(value).is_absolute())


def binding(value):
    if type(value) is not dict or set(value)!=set(BINDING):raise ValueError('Exact handoff binding required')
    for key in BINDING[:-1]:
        if not hex_string(value[key],32 if key=='transaction_nonce' else 64):raise ValueError('Invalid handoff binding: '+key)
    if not absolute_metadata(value['future_capture']):raise ValueError('Absolute future capture required')
    return value


def relative(value):
    if (type(value) is not str or not value or '\\' in value or ':' in value or PurePosixPath(value).is_absolute()
        or any(p in ('','.','..') for p in value.split('/'))):raise ValueError('Unsafe snapshot source path')
    return value


def records(rows,*,stored=False):
    if type(rows) is not list or not 1<=len(rows)<=MAX_FILES:raise ValueError('Bounded nonempty inventory required')
    seen=set();total=0
    for row in rows:
        fields={'root','path','bytes','sha256'}|({'blob'} if stored else set())
        if type(row) is not dict or set(row)!=fields:raise ValueError('Exact snapshot record required')
        if not (absolute_metadata(row['root']) if stored else type(row['root']) is str and Path(row['root']).is_absolute()):raise ValueError('Absolute snapshot root required')
        relative(row['path']);identity=(row['root'],row['path'])
        if identity in seen:raise ValueError('Duplicate snapshot source')
        seen.add(identity)
        if type(row['bytes']) is not int or not 0<=row['bytes']<=MAX_FILE or not hex_string(row['sha256'],64):raise ValueError('Invalid snapshot size or SHA')
        if stored and row['blob']!='blobs/'+row['sha256']:raise ValueError('Invalid content address')
        total+=row['bytes']
    if total>MAX_TOTAL:raise ValueError('Snapshot uncompressed budget exceeded')
    return total


def file_sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def regular_source(row):
    root=Path(row['root']);path=root/row['path']
    if root.is_symlink() or any(p.is_symlink() for p in path.parents if p==root or root in p.parents):raise ValueError('Linked snapshot root or ancestor')
    if not stat.S_ISREG(path.lstat().st_mode):raise ValueError('Snapshot source must be regular')
    return path


def summary(path,meta,sha):
    return dict(schema=SCHEMA,snapshot=str(path),snapshot_sha256=sha,snapshot_bytes=Path(path).stat().st_size,
        inventory_sha256=digest(canonical(meta)),input_files=len(meta['files']),unique_blobs=len({r['blob'] for r in meta['files']}),
        snapshot_bytes_verified=True,admission_verified=False,calculation_verified=False,gpu_calls=0,
        scope='Content integrity only; authenticated preparation, execution claim and independent audit are still required')


def freeze(inventory,out):
    if type(inventory) is not dict or set(inventory)!={'schema','binding','files'} or inventory['schema']!=INVENTORY:raise ValueError('Exact snapshot inventory required')
    binding(inventory['binding']);records(inventory['files']);out=Path(out).resolve()
    rows=sorted(inventory['files'],key=lambda r:(r['root'],r['path']))
    roots=[Path(r['root']).resolve() for r in rows]
    if any(out==p or p in out.parents or out in p.parents for p in roots):raise ValueError('Snapshot must be outside input roots')
    meta=dict(schema=SCHEMA,binding=inventory['binding'],files=[dict(r,blob='blobs/'+r['sha256']) for r in rows])
    raw=canonical(meta)
    if len(raw)>MAX_MANIFEST:raise ValueError('Snapshot manifest too large')
    # x mode deliberately retains partial files on failure; never overwrite.
    with zipfile.ZipFile(out,'x',compression=zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        written=set()
        for row in meta['files']:
            p=regular_source(row)
            if p.stat().st_size!=row['bytes']:raise ValueError('Snapshot source size changed')
            data=p.read_bytes()
            if len(data)!=row['bytes'] or digest(data)!=row['sha256']:raise ValueError('Snapshot source bytes changed')
            # Every logical source is read and checked, including duplicates.
            if row['blob'] not in written:z.writestr(row['blob'],data);written.add(row['blob'])
        z.writestr('manifest.json',raw)
    sha=file_sha(out)
    with Snapshot(out,sha) as snap:
        if snap.meta!=meta:raise ValueError('Published snapshot differs')
        for name in written:snap.read_blob(name)
    return summary(out,meta,sha)


class Snapshot:
    """Check the complete archive before use and after the read session.

    Fast validation hashes compressed bytes once rather than reopening every
    original path. Selected payloads also get a fresh uncompressed size/SHA.
    There is no extraction and no trust in paths or a hash from inside the ZIP.
    """
    def __init__(self,path,expected_sha256,*,expected_binding=None):
        self.path=Path(path);self.z=None;self.sha=expected_sha256
        if not hex_string(expected_sha256,64) or self.path.is_symlink() or not self.path.is_file() or file_sha(self.path)!=expected_sha256:raise ValueError('External snapshot SHA mismatch')
        try:
            self.z=zipfile.ZipFile(self.path);infos=self.z.infolist();names=[x.filename for x in infos]
            if len(names)!=len(set(names)) or not 2<=len(names)<=MAX_FILES+1:raise ValueError('Duplicate or excessive ZIP members')
            for info in infos:
                if info.flag_bits&1 or info.compress_type not in (zipfile.ZIP_STORED,zipfile.ZIP_DEFLATED):raise ValueError('Unsupported ZIP member')
            if self.z.getinfo('manifest.json').file_size>MAX_MANIFEST:raise ValueError('Snapshot manifest too large')
            raw=self.z.read('manifest.json');meta=json.loads(raw)
            if type(meta) is not dict or set(meta)!={'schema','binding','files'} or meta['schema']!=SCHEMA or canonical(meta)!=raw:raise ValueError('Invalid snapshot manifest')
            binding(meta['binding']);records(meta['files'],stored=True)
            if expected_binding is not None and binding(expected_binding)!=meta['binding']:raise ValueError('Snapshot binding mismatch')
            self.sizes={}
            for row in meta['files']:
                if row['blob'] in self.sizes and self.sizes[row['blob']]!=row['bytes']:raise ValueError('Conflicting blob sizes')
                self.sizes[row['blob']]=row['bytes']
            if set(names)!={'manifest.json',*self.sizes}:raise ValueError('Unlisted snapshot members')
            if any(self.z.getinfo(n).file_size!=size for n,size in self.sizes.items()):raise ValueError('ZIP size differs from inventory')
            self._meta=meta
        except BaseException:
            if self.z is not None:self.z.close()
            raise

    def __enter__(self):return self
    @property
    def meta(self):return copy.deepcopy(self._meta)
    def __exit__(self,kind,value,tb):
        self.z.close()
        if self.path.is_symlink() or not self.path.is_file() or file_sha(self.path)!=self.sha:raise ValueError('Snapshot changed during use')

    def read_blob(self,name):
        if name not in self.sizes:raise ValueError('Unknown snapshot blob')
        raw=self.z.read(name)
        if len(raw)!=self.sizes[name] or digest(raw)!=name.removeprefix('blobs/'):raise ValueError('Snapshot blob changed')
        return raw

    def read(self,root,path):
        matches=[r for r in self._meta['files'] if r['root']==str(root) and r['path']==path]
        if len(matches)!=1:raise ValueError('Unknown snapshot input')
        return self.read_blob(matches[0]['blob'])


def check(path,expected_sha256):
    with Snapshot(path,expected_sha256) as snap:return summary(path,snap.meta,expected_sha256)
