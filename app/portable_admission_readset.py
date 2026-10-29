"""Capture bytes consumed by CPU admission audits, without caching their results.

Only Path reads and the project's streaming digest are instrumented. This is
not a general filesystem tracer or proof of semantic admission. The caller
must run the original audits and require complete package closure separately.
"""
import hashlib
import inspect
import io
import os
import threading
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

_ACTIVE=threading.Lock()


class ReadSet:
    def __init__(self):
        self._rows={};self._lock=threading.Lock();self._entered=False;self._used=False

    @staticmethod
    def key(path):return Path(os.path.abspath(os.fspath(path)))

    def record(self,path,size,sha):
        key=self.key(path);row=dict(root=str(key.parent),path=key.name,bytes=size,sha256=sha)
        with self._lock:
            old=self._rows.get(key)
            if old is not None and old!=row:raise ValueError('Admission source changed between reads: '+str(key))
            self._rows[key]=row

    def __enter__(self):
        if self._used or not _ACTIVE.acquire(blocking=False):raise RuntimeError('Admission read capture already active')
        self._entered=True;self._used=True;self._stack=ExitStack()
        try:
            import portable_capture_storage as storage
            original_bytes=Path.read_bytes;original_text=Path.read_text;original_digest=storage.file_digest
            text_signature=inspect.signature(original_text)
            def read_bytes(path):
                raw=original_bytes(path);self.record(path,len(raw),hashlib.sha256(raw).hexdigest());return raw
            def read_text(path,*args,**kwargs):
                bound=text_signature.bind(path,*args,**kwargs);bound.apply_defaults()
                options={k:v for k,v in bound.arguments.items() if k!='self'}
                options['encoding']=io.text_encoding(options.get('encoding'))
                with io.TextIOWrapper(io.BytesIO(read_bytes(path)),**options) as f:return f.read()
            def file_digest(path):
                before=Path(path).stat();sha=original_digest(path);after=Path(path).stat()
                fields=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
                if fields(before)!=fields(after):raise ValueError('Admission source changed during digest: '+str(path))
                self.record(path,after.st_size,sha);return sha
            self._stack.enter_context(patch.object(Path,'read_bytes',read_bytes))
            self._stack.enter_context(patch.object(Path,'read_text',read_text))
            self._stack.enter_context(patch.object(storage,'file_digest',file_digest))
            return self
        except BaseException:
            self._stack.close();self._entered=False;_ACTIVE.release();raise

    def __exit__(self,*error):
        try:return self._stack.__exit__(*error)
        finally:self._entered=False;_ACTIVE.release()

    def rows(self):
        with self._lock:return [dict(self._rows[k]) for k in sorted(self._rows,key=str)]

    def require_package(self,root,manifest):
        """Reject an audit trace that omitted any declared immutable file.

        The caller authenticates the manifest/package ID before this method.
        No filesystem reads or implied success of the original audits here.
        """
        root=self.key(root)
        from portable_admission_snapshot import relative
        with self._lock:
            for row in manifest['files']:
                name=relative(row['path']);found=self._rows.get(self.key(root/name))
                if found is None or any(found[k]!=row[k] for k in ('bytes','sha256')):
                    raise ValueError('Incomplete admission package read set: '+name)
