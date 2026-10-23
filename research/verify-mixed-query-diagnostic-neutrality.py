"""CPU-only full-byte comparison of finished normal/diagnostic mixed captures."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

STRIDE=786432*4
# Explicit observer bank only. Cache, part receipts and interrupt sums stay compared.
START=771072*4
END=(771072+8+512*20)*4


def verify(normal,diagnostic):
    if sys.flags.optimize:raise RuntimeError("Assertions must be enabled for a neutrality audit")
    normal,diagnostic=Path(normal),Path(diagnostic)
    reports=[json.loads((p/'comparison.json').read_text()) for p in (normal,diagnostic)]
    for path,report in zip((normal,diagnostic),reports):
        assert json.loads((path/'run.json').read_text())['status']=='finished'
        assert report['calculation_verified'] and not report['mismatches']
        for name,key in (('input.bin','input_sha256'),('readback.bin','output_sha256')):
            assert hashlib.sha256((path/name).read_bytes()).hexdigest()==report[key]
    assert (normal/'input.bin').read_bytes()==(diagnostic/'input.bin').read_bytes()
    assert [(r['name'],r['native_sha256']) for r in reports[0]['entries']]==[(r['name'],r['native_sha256']) for r in reports[1]['entries']]
    raw=[(p/'readback.bin').read_bytes() for p in (normal,diagnostic)]
    count=len(reports[0]['entries'])
    assert count==6 and all(len(b)==count*STRIDE for b in raw)
    for i in range(count):
        a,b=[data[i*STRIDE:(i+1)*STRIDE] for data in raw]
        assert a[:START]==b[:START] and a[END:]==b[END:],('diagnostic changed battle bytes',i)
        assert not any(a[START:END]),'normal entry wrote diagnostic bank'
    return dict(passed=True,gpu_calls=0,cases=count,input_sha256=reports[0]['input_sha256'],
                normal_output_sha256=reports[0]['output_sha256'],diagnostic_output_sha256=reports[1]['output_sha256'],
                excluded_observer_word_range=[START//4,END//4],
                unchanged_bytes=count*(STRIDE-(END-START)),
                scope='Exact native identities and every byte outside explicit heal diagnostic bank')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--normal',required=True);parser.add_argument('--diagnostic',required=True);parser.add_argument('--out',required=True)
    args=parser.parse_args();report=verify(args.normal,args.diagnostic)
    with Path(args.out).open('x') as stream:json.dump(report,stream,indent=2);stream.write('\n')
    print(json.dumps(report,indent=2))
