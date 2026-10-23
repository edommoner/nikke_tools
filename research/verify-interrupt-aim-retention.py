"""CPU-only old-byte retention and private interrupt observer neutrality audit."""
import argparse,array,hashlib,json,sys
from pathlib import Path
load=lambda p:json.loads(Path(p).read_text())


def verify(old,new,diag,mixed,rejection_stage):
    if sys.flags.optimize:raise RuntimeError('Assertions must be enabled for retained-byte verification')
    old,new,diag,mixed=map(Path,(old,new,diag,mixed))
    for path in (old,new,diag,mixed):
        run=load(path/'run.json')
        assert run['status']=='finished' and run['backend']=='metal','unfinished or non-Metal capture'
    sources=[load(path/'evidence.json')['source_sha256'] for path in (new,diag)]
    assert all(sources[1].get(k)==v for k,v in sources[0].items()),'different shared GPU sources'
    stage=load(rejection_stage)
    assert stage['name']=='state-focus/reject/state-focus-physical-interrupt' and stage['index']==1327
    assert stage['before_status']==stage['after_status']==64 and len(stage['word_changes'])==657
    a,b,c=[load(p/'comparison.json') for p in (old,new,diag)]
    for r in (a,b,c):assert r['calculation_verified'] and not r['mismatches']
    assert [len(r['entries']) for r in (a,b,c)]==[1355,1385,24]
    stride=786432*4;oldhash=hashlib.sha256();newhash=hashlib.sha256();diaghash=hashlib.sha256();n=0
    with (old/'readback.bin').open('rb') as os,(new/'readback.bin').open('rb') as ns,(diag/'readback.bin').open('rb') as ds:
     for i,row in enumerate(a['entries']):
      current=b['entries'][i]
      assert current['name']=='ordered-history-retention/'+row['name']
      for field in ('input_sha256','native_sha256'):assert current.get(field)==row.get(field),(i,field)
      x,y=os.read(stride),ns.read(stride)
      assert len(x)==len(y)==stride
      if i==stage['index']:
       assert row['name']==stage['name']
       assert row['input_sha256']==stage['input_sha256'] and row['native_sha256']==stage['native_sha256']
       assert row['output_sha256']==stage['before_output_sha256'] and current['output_sha256']==stage['after_output_sha256']
       words=[]
       for data in (x,y):
        v=array.array('I');v.frombytes(data)
        if sys.byteorder!='little':v.byteswap()
        words.append(v)
       assert words[0][0]==words[1][0]==64
       changes=[dict(word=j,before=v,after=w) for j,(v,w) in enumerate(zip(*words)) if v!=w]
       assert changes==stage['word_changes'] and all(r['before']==0 for r in changes),'unreviewed rejection state changes'
       n+=len(x)-len(changes)*4
      else:
       assert x==y and current['output_sha256']==row['output_sha256'],('old bytes',i)
       n+=len(x)
      oldhash.update(x);newhash.update(y)
     assert os.read(1)==b''
     start,end=785536*4,(785536+16+16*32)*4
     for i,row in enumerate(c['entries']):
      current=b['entries'][1355+i]
      assert current['name']=='interrupt-aim/'+row['name']
      for field in ('input_sha256','native_sha256'):assert current[field]==row[field]
      x,y=ns.read(stride),ds.read(stride)
      assert len(x)==len(y)==stride
      assert x[:start]==y[:start] and x[end:]==y[end:],('diagnostic changed battle',i)
      assert not any(x[start:end]),'normal wrote diagnostic bank'
      newhash.update(x);diaghash.update(y)
     assert ds.read(1)==b''
     mixed_report=load(mixed/'comparison.json');mixed_hash=hashlib.sha256()
     assert mixed_report['calculation_verified'] and len(mixed_report['entries'])==6
     with (mixed/'readback.bin').open('rb') as ms:
      for i,row in enumerate(mixed_report['entries']):
       current=b['entries'][1379+i]
       assert current['name']=='mixed-query/'+row['name']
       for field in ('input_sha256','native_sha256','output_sha256'):assert current[field]==row[field]
       data,prior=ns.read(stride),ms.read(stride);assert len(data)==stride and data==prior,('mixed bytes',i)
       newhash.update(data);mixed_hash.update(prior)
      assert ms.read(1)==b''
     assert mixed_hash.hexdigest()==mixed_report['output_sha256']
     assert ns.read(1)==b''
    assert oldhash.hexdigest()==a['output_sha256']
    assert newhash.hexdigest()==b['output_sha256']
    assert diaghash.hexdigest()==c['output_sha256']
    report=dict(passed=True,gpu_calls=0,old_cases=1355,old_full_byte_equal_cases=1354,changed_rejection_cases=1,changed_rejection_words=657,old_unchanged_bytes=n,
     old_output_sha256=oldhash.hexdigest(),new_output_sha256=newhash.hexdigest(),diagnostic_output_sha256=diaghash.hexdigest(),
     mixed_cases=6,mixed_unchanged_bytes=6*stride,mixed_output_sha256=mixed_hash.hexdigest(),diagnostic_cases=24,diagnostic_only_word_range=[start//4,end//4],diagnostic_unchanged_bytes=24*(stride-(end-start)),
     scope='Actual old raw bytes, unchanged input/native identities and every byte outside the explicit observer bank')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for key in ('old','new','diagnostic','mixed','rejection-stage','out'):parser.add_argument('--'+key,required=True,type=Path)
    args=parser.parse_args();report=verify(args.old,args.new,args.diagnostic,args.mixed,args.rejection_stage)
    with args.out.open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report,indent=2))
