"""Exact041934b aimed-factor transition audit; never a result normalizer."""
import array,hashlib,json,sys
from pathlib import Path
load=lambda p:json.loads(Path(p).read_text())


def validate_sources(root,before,after,diagnostic):
    from portable_aimed_factor_source_contract import ledger
    rows=ledger(root)['sources']
    for name,row in rows.items():
        if before.get(name)!=row['baseline_sha256'] or after.get(name)!=row['current_sha256']:
            raise ValueError('Capture differs from reviewed aimed factor transition: '+name)
    if {k:v for k,v in before.items() if k not in rows}!={k:v for k,v in after.items() if k not in rows}:
        raise ValueError('GPU source changed outside aimed factor consumer')
    if not all(diagnostic.get(k)==v for k,v in after.items()):
        raise ValueError('Diagnostic and normal shared sources differ')
    if any('diagnostic_entry.slang' in k or 'window_entry.slang' in k for k in after):
        raise ValueError('Ordinary resident captures required for retention')


def compare_captures(root,before,after,diagnostic):
    if sys.flags.optimize:raise RuntimeError('Assertions required for saved-result verification')
    old,new,diag=map(Path,(before,after,diagnostic))
    for path in (old,new,diag):
        run=load(path/'run.json')
        assert run['status']=='finished' and run['backend']=='metal','unfinished or non-Metal capture'
        report=load(path/'comparison.json');data=path/'input.bin'
        assert data.stat().st_size==4+len(report['entries'])*104400*4,'input corpus size'
        with data.open('rb') as stream:
            assert int.from_bytes(stream.read(4),'little')==len(report['entries'])
        with data.open('rb') as stream:
            assert hashlib.file_digest(stream,'sha256').hexdigest()==report['input_sha256'],'input corpus hash'
    validate_sources(root,*[load(path/'evidence.json')['source_sha256'] for path in (old,new,diag)])
    a,b,c=[load(p/'comparison.json') for p in (old,new,diag)]
    assert all(r['calculation_verified'] and not r['mismatches'] for r in (a,b,c))
    assert [len(r['entries']) for r in (a,b,c)]==[1385,1393,8]
    stride=786432*4;memo={21088+who*16+j for who in range(5) for j in (8,9,10,11,12)}
    hashes=[hashlib.sha256() for _ in range(3)];changed=[];equal=0;unchanged=0
    with (old/'readback.bin').open('rb') as os,(new/'readback.bin').open('rb') as ns,(diag/'readback.bin').open('rb') as ds:
     for i,row in enumerate(a['entries']):
      current=b['entries'][i];assert current['name']=='interrupt-aim-retention/'+row['name']
      for key in ('input_sha256','native_sha256'):assert current.get(key)==row.get(key),(i,key)
      x,y=os.read(stride),ns.read(stride);assert len(x)==len(y)==stride
      hashes[0].update(x);hashes[1].update(y)
      if x==y:equal+=1;unchanged+=stride;continue
      words=[]
      for data in (x,y):
       v=array.array('I');v.frombytes(data)
       if sys.byteorder!='little':v.byteswap()
       words.append(v)
      diffs=[dict(word=j,before=v,after=w) for j,(v,w) in enumerate(zip(*words)) if v!=w]
      assert all(r['word'] in memo for r in diffs),('unexpected changed numerical output',i,diffs)
      changed.append(dict(index=i,name=row['name'],before_sha256=row['output_sha256'],after_sha256=current['output_sha256'],word_changes=diffs))
      unchanged+=stride-4*len(diffs)
     assert os.read(1)==b''
     start,end=785536*4,786064*4
     for i,row in enumerate(c['entries']):
      current=b['entries'][1385+i];assert current['name']=='aimed-factor/'+row['name']
      for key in ('input_sha256','native_sha256'):assert current[key]==row[key]
      x,y=ns.read(stride),ds.read(stride);assert len(x)==len(y)==stride
      assert x[:start]==y[:start] and x[end:]==y[end:],('diagnostic changed battle bytes',i)
      assert not any(x[start:end]);hashes[1].update(x);hashes[2].update(y)
     assert ns.read(1)==ds.read(1)==b''
    for h,r in zip(hashes,(a,b,c)):assert h.hexdigest()==r['output_sha256']
    report=dict(passed=True,gpu_calls=0,old_native_and_input_cases=1385,old_full_byte_equal=equal,old_changed_memo_cases=len(changed),unchanged_old_bytes=unchanged,
     memo_only_word_offsets=sorted(memo),changed_memo_rows=changed,source_scope='Explicit per-weapon lastSpread/lastProbability/probabilityEvaluations; no numerical result normalization',
     output_sha256={k:h.hexdigest() for k,h in zip(('old','new','diagnostic'),hashes)},diagnostic_cases=8,diagnostic_unchanged_bytes=8*(stride-(end-start)),diagnostic_only_word_range=[start//4,end//4])
    return report
