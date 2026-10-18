"""Check that positive CPU mechanics were exercised, not merely no-op equality."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
r=json.loads((ROOT/'research/detail-cleanse-cpu-references.json').read_text(encoding='utf-8'))
rows={c['name']:c for c in r['cases']};names=r['cases'][0]['input']['squad']
def removed(case):
 call=rows[case]['cleanups'][0];after={ab['uid']:ab for ab in call['after']}
 return {n:sum(n in (ab['targets'] or []) and n not in (after.get(ab['uid'],{}).get('targets') or []) for ab in call['before'] if ab['polarity']=='harmful') for n in names}
checks={}
for val,count in [('1',1),('2',2),('0',2),('-1',2),('None',2),('0.5',1)]:
 checks['limit-'+val]=all(x==count for x in removed('per-recipient-limit-'+val).values())
checks['partial-right']=removed('partial-right-recipients')=={n:int(i in (1,2)) for i,n in enumerate(names)}
checks['duplicate-target']=removed('duplicate-recipient-does-not-consume-again')=={n:int(i in (0,1)) for i,n in enumerate(names)}
checks['no-end-notification']=all(not call['notifications'] for case in r['cases'] for call in case['cleanups'])
call=rows['partial-shield-carrier-preserves-maps']['cleanups'][0]
before=next(ab for ab in call['before'] if ab['name']=='harmful shield');after=next(ab for ab in call['after'] if ab['uid']==before['uid'])
checks['shield-maps-retained']=before['shield']==after['shield'] and names[0] in after['shield'] and names[0] not in after['targets']
call=rows['periodic-damage-cleanse-retains-timer']['cleanups'][0]
checks['dot-timer-retained']=bool(call['timers_before']) and call['timers_before']==call['timers_after'] and removed('periodic-damage-cleanse-retains-timer')=={n:1 for n in names}
call=rows['lazy-unresolved-is-not-stripped']['cleanups'][0]
checks['unresolved-lazy-retained']=any(ab['name']=='lazy harm' and ab['targets'] is None for ab in call['before']) and any(ab['name']=='lazy harm' and ab['targets'] is None for ab in call['after'])
assert all(checks.values()),checks
out={'passed':True,'cpu_reference_only':True,'gpu_implemented':False,'cases':len(r['cases']),'checks':checks,
     'remaining':['Port per-recipient old-instance selection without ended events or timer removal','Preserve shield and bullet maps on partial removal','Random harmful-recipient selection needs GPU PRNG parity before accepting Cocoa; do not silently select leftmost recipients'],
     'source_sha256':{**r['source_sha256'],'research/detail-cleanse-cpu-references.json':hashlib.sha256((ROOT/'research/detail-cleanse-cpu-references.json').read_bytes()).hexdigest()}}
(ROOT/'research/detail-cleanse-semantics.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out))
