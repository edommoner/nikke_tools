"""CPU-only block index/diff for saved readbacks; never executes a GPU."""
import argparse,hashlib,json,struct
from pathlib import Path

SCHEMA='readback-block-index-v1'
CASE_WORDS=786432
BLOCK_WORDS=1024


def digest(raw):return hashlib.sha256(raw).hexdigest()


def checked_hash(value):
    if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('Expected lowercase SHA256')
    return value


def scan(path,expected_sha256):
    checked_hash(expected_sha256);h=hashlib.sha256();size=0;blocks=[]
    with Path(path).open('rb') as stream:
        while True:
            raw=stream.read(BLOCK_WORDS*4)
            if not raw:break
            h.update(raw);size+=len(raw);blocks.append(digest(raw))
    if not size or size%(CASE_WORDS*4) or h.hexdigest()!=expected_sha256:raise ValueError('Readback size or recorded SHA mismatch')
    return dict(schema=SCHEMA,bytes=size,sha256=h.hexdigest(),case_words=CASE_WORDS,block_words=BLOCK_WORDS,cases=size//(CASE_WORDS*4),blocks=blocks)


def validate(index):
    if index['schema']!=SCHEMA or index['case_words']!=CASE_WORDS or index['block_words']!=BLOCK_WORDS or type(index['cases']) is not int or index['cases']<=0 or index['bytes']!=index['cases']*CASE_WORDS*4 or len(index['blocks'])*BLOCK_WORDS*4!=index['bytes']:raise ValueError('Invalid fixed readback block index')
    checked_hash(index['sha256'])
    for value in index['blocks']:checked_hash(value)


def compare(path,expected_sha256,index,*,sample_blocks=8):
    validate(index)
    if type(sample_blocks) is not int or not 0<=sample_blocks<=8:raise ValueError('At most eight sampled diagnostic blocks')
    actual=scan(path,expected_sha256)
    if actual['bytes']!=index['bytes']:raise ValueError('Readback case count mismatch')
    changed=[i for i,(a,b) in enumerate(zip(actual['blocks'],index['blocks'],strict=True)) if a!=b]
    rows=[]
    # Recheck all bytes while extracting bounded samples; never trust a second
    # pass after the file changed between scan and sampling.
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        selected=set(changed[:sample_blocks])
        for i,want in enumerate(actual['blocks']):
            raw=stream.read(BLOCK_WORDS*4);h.update(raw)
            if digest(raw)!=want:raise ValueError('Readback changed while sampling')
            if i in selected:rows.append(dict(block=i,case_index=i*BLOCK_WORDS//CASE_WORDS,case_word_offset=i*BLOCK_WORDS%CASE_WORDS,words=list(struct.unpack('<'+str(BLOCK_WORDS)+'I',raw))))
        if stream.read(1) or h.hexdigest()!=actual['sha256']:raise ValueError('Readback changed while sampling')
    return dict(schema='readback-block-diff-v1',reference_sha256=index['sha256'],actual_sha256=actual['sha256'],bytes=actual['bytes'],blocks=len(actual['blocks']),changed_blocks=changed,samples=rows,all_blocks_equal=not changed,gpu_calls=0,calculation_verified=False)


def write(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(value,stream,separators=(',',':'));stream.write('\n')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for name in ('index','compare'):
        a=sub.add_parser(name);a.add_argument('--readback',type=Path,required=True);a.add_argument('--sha256',required=True);a.add_argument('--out',type=Path,required=True)
        if name=='compare':a.add_argument('--index',type=Path,required=True);a.add_argument('--index-sha256',required=True)
    a=p.parse_args(argv)
    if a.command=='index':result=scan(a.readback,a.sha256)
    else:
        raw=a.index.read_bytes()
        if digest(raw)!=checked_hash(a.index_sha256):raise ValueError('Reference index SHA mismatch')
        result=compare(a.readback,a.sha256,json.loads(raw))
    write(a.out,result)
    print(json.dumps(dict(saved=str(a.out),sha256=digest(a.out.read_bytes()),gpu_calls=0,changed_blocks=len(result.get('changed_blocks',[])),all_blocks_equal=result.get('all_blocks_equal'))))


if __name__=='__main__':main()
