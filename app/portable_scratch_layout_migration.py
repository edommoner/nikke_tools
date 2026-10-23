"""Explicit4436fbf scratch relocation audit; never a result normalizer."""
import array,hashlib,json
from pathlib import Path

def validate_sources(root,old,new):
    from portable_scratch_layout_source_contract import ledger
    before=json.loads((old/'evidence.json').read_text())['source_sha256']
    after=json.loads((new/'evidence.json').read_text())['source_sha256']
    rows=ledger(root)['sources']
    empty=hashlib.sha256(b'').hexdigest()
    for name,row in rows.items():
        expected=None if row['baseline_sha256']==empty else row['baseline_sha256']
        if before.get(name)!=expected or after.get(name)!=row['current_sha256']:
            raise ValueError('Capture does not match the reviewed layout transition: '+name)
    if {n:h for n,h in before.items() if n not in rows}!={n:h for n,h in after.items() if n not in rows}:
        raise ValueError('GPU source changed outside the layout relocation')
    if any('diagnostic_entry.slang' in n or 'window_entry.slang' in n for n in after):
        raise ValueError('This migration audit requires ordinary resident captures')

def compare_captures(root,before,after):
    old,new=Path(before),Path(after)
    a=json.loads((old/'comparison.json').read_text());b=json.loads((new/'comparison.json').read_text());
    validate_sources(root,old,new)
    assert a['calculation_verified'] and b['calculation_verified'];assert len(a['entries'])==len(b['entries'])>0
    for capture in (old,new):
        data=capture/'input.bin'
        assert data.stat().st_size==4+len(a['entries'])*104400*4,'input size'
        with data.open('rb') as stream:
            assert int.from_bytes(stream.read(4),'little')==len(a['entries']),'input count'
        with data.open('rb') as stream:
            digest=hashlib.file_digest(stream,'sha256').hexdigest()
        expected=a if capture==old else b
        assert digest==expected['input_sha256'],'input file digest'
    assert a['input_sha256']==b['input_sha256'],'input corpus changed'
    before_hash,after_hash=hashlib.sha256(),hashlib.sha256()
    size=786432*4;rows=[];total_equal=0;total_fixed=0;focus_cases=numeric_cases=history_cases=cells=0

    def merge(ranges):
     out=[]
     for start,end in sorted(ranges):
      if out and start<=out[-1][1]:out[-1]=(out[-1][0],max(end,out[-1][1]))
      else:out.append((start,end))
     return out

    with (old/'readback.bin').open('rb') as left,(new/'readback.bin').open('rb') as right:
     for before,after in zip(a['entries'],b['entries'],strict=True):
      assert before['name']==after['name'];assert before['input_sha256']==after['input_sha256'];assert before['native_sha256']==after['native_sha256']
      x=left.read(size);y=right.read(size);assert len(x)==len(y)==size
      before_hash.update(x);after_hash.update(y)
      assert hashlib.sha256(x).hexdigest()==before['output_sha256'];assert hashlib.sha256(y).hexdigest()==after['output_sha256']
      p=array.array('I');p.frombytes(x);q=array.array('I');q.frombytes(y);ranges=[];flags=[]
      if p[770976+6]==0x46414331 or p[770976+8]==1:
       assert p[770976:773056]==q[258576:260656],(before['name'],'focus cache relocation')
       ranges.extend([(770976,773056),(258576,260656)]);focus_cases+=1;flags.append('focus')
      if p[773056]==0x4e515231:
       assert p[773056:773088]==q[785440:785472],(before['name'],'numeric header relocation')
       count=p[773056+2];assert count<=64
       for i in range(count):
        src=773088+i*136;dst=(248600+i*136) if i<32 else (518336+(i-32)*136)
        assert p[src:src+136]==q[dst:dst+136],(before['name'],'live full dictionary',i);cells+=1
       assert p[781792:781856]==q[785472:785536],(before['name'],'ordered history relocation')
       ranges.extend([(773056,781856),(248600,252952),(518336,522688),(785440,785536)]);numeric_cases+=1;flags.append('numeric/history')
       history_cases+=int(p[781792]==0x4f485331)
      end=0;fixed=0
      for start,stop in merge(ranges)+[(786432,786432)]:
       assert x[end*4:start*4]==y[end*4:start*4],(before['name'],'change outside declared relocated scratch',end,start)
       fixed+=(start-end)*4;end=stop
      total_fixed+=fixed
      if x==y:total_equal+=1
      rows.append(dict(name=before['name'],relocated=flags,unchanged_outside_relocated_bytes=fixed))
     assert not left.read(1) and not right.read(1)
    assert before_hash.hexdigest()==a['output_sha256'] and after_hash.hexdigest()==b['output_sha256'],'whole readback digest'
    r=dict(passed=True,gpu_calls=0,scope='Full native/input fingerprints and bytes outside explicit scratch relocation; no normalizer changes',cases=len(a['entries']),full_byte_equal_cases=total_equal,focus_cases=focus_cases,numeric_cases=numeric_cases,long_history_cases=history_cases,full_live_dictionary_cells_verified=cells,unchanged_fixed_bytes=total_fixed,before_output_sha256=before_hash.hexdigest(),after_output_sha256=after_hash.hexdigest(),rows=rows)
    return r
