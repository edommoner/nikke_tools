"""Record/check unchanged v1/v2 outputs without opening S22 truth."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import time
import l2_fast
import truth_s22 as truth


def run(out):
    started=time.perf_counter()
    rows=[json.loads(l)['members'] for name in ('s9-dataset.jsonl','s1-results.jsonl')
          for l in (truth.HERE/name).read_text().splitlines()]
    result={}
    for version,path in [('v1',out.parent/'s18/profiles.json'),('v2',out.parent/'s20/dev/final-profiles.json')]:
        scorer=l2_fast.Score.load(path)
        h=hashlib.sha256()
        for offset in range(0,len(rows),1024):
            totals,members=scorer.score_indices(scorer._indices(rows[offset:offset+1024]),True)
            for i,total in enumerate(totals):h.update(struct.pack('<6d',total,*members[i*5:i*5+5]))
        result[version]=dict(rows=len(rows),raw6d_sha256=h.hexdigest(),table_sha256=hashlib.sha256(scorer.raw).hexdigest())
        scorer.close()
    entries=[]
    for n in (150,206):
        for mask in (15,2):
            scorer=l2_fast.Score(truth.previous.profiles(out,mask))
            source=truth.previous.read(out.parent/f's21/native-{n}-{mask}-10-1.json')['entries']
            squads=[[scorer.names[i] for i in r['indices']] for r in source]
            scores=scorer.score_many(squads)
            assert all(struct.pack('<d',a)==struct.pack('<d',b['score']) for a,b in zip(scores,source))
            orders=truth.previous.read(out.parent/f's21/orders-{n}-{mask}.json')['rows']
            for key in ('canonical','best'):
                squads=[[scorer.names[i] for i in (r['indices'] if key=='canonical' else r['best']['indices'])] for r in orders]
                scores=scorer.score_many(squads)
                assert all(a==(r['canonical_score'] if key=='canonical' else r['best']['score']) for a,r in zip(scores,orders))
            entries.append(dict(n=n,mask=mask,entries=len(source),canonical_and_best=len(orders)*2,differences=0))
            scorer.close()
    result['S21']=entries
    return dict(outputs=result,seconds=time.perf_counter()-started)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('record','check'))
    parser.add_argument('--out',type=Path,default=truth.previous.DEFAULT/'s22')
    a=parser.parse_args();result=run(a.out)
    if a.action=='record':
        with (a.out/'frozen-before.json').open('x') as f:json.dump(result,f,indent=2)
    else:
        assert result['outputs']==truth.previous.read(a.out/'frozen-before.json')['outputs']
        truth.save(a.out/'frozen-after.json',result)
    print(json.dumps(result))
