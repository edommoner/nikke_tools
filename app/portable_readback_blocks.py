"""CPU-only block index/diff for saved readbacks; never executes a GPU."""
import argparse,hashlib,json,struct
from pathlib import Path

SCHEMA='readback-block-index-v1'
CASE_WORDS=786432
CASE_SHAPES=(CASE_WORDS,1048576)
BLOCK_WORDS=1024


def digest(raw):return hashlib.sha256(raw).hexdigest()


def checked_hash(value):
    if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):raise ValueError('Expected lowercase SHA256')
    return value


def scan(path,expected_sha256,*,case_words=CASE_WORDS,include_case_hashes=False):
    if type(case_words) is not int or case_words not in CASE_SHAPES:raise ValueError('Unsupported readback case shape')
    checked_hash(expected_sha256);h=hashlib.sha256();case=hashlib.sha256();size=0;blocks=[];cases=[]
    with Path(path).open('rb') as stream:
        while True:
            raw=stream.read(BLOCK_WORDS*4)
            if not raw:break
            h.update(raw);size+=len(raw);blocks.append(digest(raw))
            if include_case_hashes:
                case.update(raw)
                if size%(case_words*4)==0:cases.append(case.hexdigest());case=hashlib.sha256()
    if not size or size%(case_words*4) or h.hexdigest()!=expected_sha256:raise ValueError('Readback size or recorded SHA mismatch')
    result=dict(schema=SCHEMA,bytes=size,sha256=h.hexdigest(),case_words=case_words,block_words=BLOCK_WORDS,cases=size//(case_words*4),blocks=blocks)
    if include_case_hashes:result['case_sha256']=cases
    return result


def validate(index):
    if index['schema']!=SCHEMA or type(index['case_words']) is not int or index['case_words'] not in CASE_SHAPES or index['block_words']!=BLOCK_WORDS or type(index['cases']) is not int or index['cases']<=0 or index['bytes']!=index['cases']*index['case_words']*4 or len(index['blocks'])*BLOCK_WORDS*4!=index['bytes']:raise ValueError('Invalid fixed readback block index')
    checked_hash(index['sha256'])
    for value in index['blocks']:checked_hash(value)


def compare(path,expected_sha256,index,*,sample_blocks=8):
    validate(index)
    if type(sample_blocks) is not int or not 0<=sample_blocks<=8:raise ValueError('At most eight sampled diagnostic blocks')
    actual=scan(path,expected_sha256,case_words=index['case_words'])
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
            if i in selected:rows.append(dict(block=i,case_index=i*BLOCK_WORDS//index['case_words'],case_word_offset=i*BLOCK_WORDS%index['case_words'],words=list(struct.unpack('<'+str(BLOCK_WORDS)+'I',raw))))
        if stream.read(1) or h.hexdigest()!=actual['sha256']:raise ValueError('Readback changed while sampling')
    return dict(schema='readback-block-diff-v1',reference_sha256=index['sha256'],actual_sha256=actual['sha256'],bytes=actual['bytes'],blocks=len(actual['blocks']),changed_blocks=changed,samples=rows,all_blocks_equal=not changed,gpu_calls=0,calculation_verified=False)


def capture_fingerprints(folder,comparison_sha256,case_words):
    raw=(Path(folder)/'comparison.json').read_bytes()
    if digest(raw)!=checked_hash(comparison_sha256):raise ValueError('Comparison anchor SHA mismatch')
    report=json.loads(raw);entries=report['entries']
    if report.get('calculation_verified') is not True or report.get('mismatches')!=[] or type(report.get('input_count')) is not int or not isinstance(entries,list) or report['input_count']!=len(entries):raise ValueError('Expected a successful complete comparison')
    names=set()
    for row in entries:
        name=row['name']
        if not isinstance(name,str) or not name or name in names:raise ValueError('Invalid or duplicate case name')
        names.add(name)
        for key in ('input_sha256','native_sha256','output_sha256'):checked_hash(row[key])
    index=scan(Path(folder)/'readback.bin',report['output_sha256'],case_words=case_words,include_case_hashes=True)
    if index['cases']!=len(entries):raise ValueError('Comparison/readback case count mismatch')
    if [row['output_sha256'] for row in entries]!=index['case_sha256']:raise ValueError('Comparison case fingerprint differs from actual readback')
    return report,index


def retain(reference,reference_comparison_sha256,candidate,candidate_comparison_sha256,*,case_words=CASE_WORDS):
    """Rehash both complete files; compare retained cases by anchored name.

    This checks preserved bytes/input/native fingerprints, never recomputes a
    numerical oracle or converts a report's success flag into a GPU proof.
    """
    old,old_index=capture_fingerprints(reference,reference_comparison_sha256,case_words)
    new,new_index=capture_fingerprints(candidate,candidate_comparison_sha256,case_words)
    previous={r['name']:r for r in old['entries']};current={r['name']:r for r in new['entries']}
    missing=sorted(previous.keys()-current.keys());added=sorted(current.keys()-previous.keys());changed=[]
    for name,row in previous.items():
        if name not in current:continue
        fields=[key for key in ('input_sha256','native_sha256','output_sha256') if row[key]!=current[name][key]]
        if fields:changed.append(dict(name=name,fields=fields))
    return dict(schema='readback-case-retention-v1',reference_comparison_sha256=reference_comparison_sha256,candidate_comparison_sha256=candidate_comparison_sha256,reference_readback_sha256=old_index['sha256'],candidate_readback_sha256=new_index['sha256'],case_words=case_words,reference_cases=len(previous),candidate_cases=len(current),retained_cases=len(previous)-len(missing)-len(changed),retained_output_bytes=(len(previous)-len(missing)-len(changed))*case_words*4,missing=missing,added=added,changed=changed,all_reference_cases_retained=not missing and not changed,gpu_calls=0,calculation_verified=False)


def write(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(value,stream,separators=(',',':'));stream.write('\n')


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    for name in ('index','compare'):
        a=sub.add_parser(name);a.add_argument('--readback',type=Path,required=True);a.add_argument('--sha256',required=True);a.add_argument('--out',type=Path,required=True)
        if name=='compare':a.add_argument('--index',type=Path,required=True);a.add_argument('--index-sha256',required=True)
        else:a.add_argument('--case-words',type=int,choices=CASE_SHAPES,default=CASE_WORDS)
    a=sub.add_parser('retain');a.add_argument('--reference-capture',type=Path,required=True);a.add_argument('--reference-comparison-sha256',required=True);a.add_argument('--candidate-capture',type=Path,required=True);a.add_argument('--candidate-comparison-sha256',required=True);a.add_argument('--case-words',type=int,choices=CASE_SHAPES,default=CASE_WORDS);a.add_argument('--out',type=Path,required=True)
    a=p.parse_args(argv)
    if a.command=='index':result=scan(a.readback,a.sha256,case_words=a.case_words)
    elif a.command=='retain':result=retain(a.reference_capture,a.reference_comparison_sha256,a.candidate_capture,a.candidate_comparison_sha256,case_words=a.case_words)
    else:
        raw=a.index.read_bytes()
        if digest(raw)!=checked_hash(a.index_sha256):raise ValueError('Reference index SHA mismatch')
        result=compare(a.readback,a.sha256,json.loads(raw))
    write(a.out,result)
    print(json.dumps(dict(saved=str(a.out),sha256=digest(a.out.read_bytes()),gpu_calls=0,changed_blocks=len(result.get('changed_blocks',[])),all_blocks_equal=result.get('all_blocks_equal'),all_reference_cases_retained=result.get('all_reference_cases_retained'))))
    if a.command=='retain' and not result['all_reference_cases_retained']:raise SystemExit(2)


if __name__=='__main__':main()
