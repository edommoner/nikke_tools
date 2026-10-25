"""Verify an explicitly registered literal-only input extension, GPU0."""
import hashlib,struct
from pathlib import Path

def _scan(folder,report,words,keep=None):
    path=Path(folder)/'input.bin'
    if path.is_symlink():raise ValueError('Input extension audit rejects symlinks')
    stamp=path.stat();whole=hashlib.sha256();answers={}
    with path.open('rb') as stream:
        header=stream.read(4);whole.update(header)
        if len(header)!=4 or int.from_bytes(header,'little')!=len(report['entries']):raise ValueError('Input extension case count mismatch')
        for row in report['entries']:
            raw=stream.read(words*4);whole.update(raw)
            if len(raw)!=words*4 or hashlib.sha256(raw).hexdigest()!=row['input_sha256']:raise ValueError('Input extension case fingerprint mismatch')
            if keep is None or row['name'] in keep:answers[row['name']]=raw
        if stream.read(1) or whole.hexdigest()!=report['input_sha256']:raise ValueError('Input extension whole-file fingerprint mismatch')
    after=path.stat()
    if (stamp.st_dev,stamp.st_ino,stamp.st_size,stamp.st_mtime_ns)!=(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns):raise ValueError('Input extension capture changed while reading')
    return answers

def verify_extension(reference,old,candidate,new,contract):
    if contract!='coordinate-policy-v1':raise ValueError('Unknown input extension contract')
    from portable_cover_policy_specs import INPUT_BASE,INPUT_WORDS,empty
    previous=_scan(reference,old,INPUT_BASE);current=_scan(candidate,new,INPUT_BASE+INPUT_WORDS,set(previous))
    suffix=struct.pack('<'+str(INPUT_WORDS)+'I',*empty());equivalent={}
    for name,raw in previous.items():
        if name not in current:continue
        value=current[name];equivalent[name]=value[:INPUT_BASE*4]==raw and value[INPUT_BASE*4:]==suffix
    return equivalent,dict(contract=contract,input_prefix_words=INPUT_BASE,appended_input_words=INPUT_WORDS,appended_input_literal_sha256=hashlib.sha256(suffix).hexdigest(),all_inputs_rehashed=True,gpu_calls=0)
