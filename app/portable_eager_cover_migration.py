"""Audit the four selector25 lazy-bit corrections against immutable old inputs."""
import array,hashlib,json,sys
from pathlib import Path
from portable_specs import LIMITS as L


def wire(words):
    result=array.array('I',words)
    if sys.byteorder!='little':result.byteswap()
    return result.tobytes()


def historical_words(root,name,words):
    data=json.loads((Path(root)/'tests/fixtures/portable-eager-cover-input-migration.json').read_text())
    row=data['changed_cases'].get(name)
    if row is None:return list(words)
    assert hashlib.sha256(wire(words)).hexdigest()==row['after_sha256'],'Unreviewed eager-cover input'
    restored=list(words)
    for change in row['changes']:
        at=change['word'];old=change['before'];new=change['after']
        assert at>=L['RECIPIENT_BASE'] and (at-L['RECIPIENT_BASE'])%8==7,'Migration outside recipient flags'
        plan=at-7
        assert restored[plan]==25 and old>>4>0 and new==old&15,'Migration must only clear selector25 lazy group'
        assert restored[at]==new,'Eager-cover new flags differ'
        restored[at]=old
    assert hashlib.sha256(wire(restored)).hexdigest()==row['before_sha256'],'Eager-cover historical bytes differ'
    return restored
