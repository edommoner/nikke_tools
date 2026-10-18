"""Paired CPU battle timing for precomputed lifecycle callback dispatch only."""
import hashlib,json,statistics,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from effect_runtime import Catalog

def scanning_emit(self,phase,manager,*args):
    if not self.sealed:raise RuntimeError('Lifecycle catalog is not sealed')
    for spec in self.specs:
        callback=getattr(self.handlers[spec.key],phase)
        if callback is not None:callback(manager,*args)

files=sorted({str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'app').glob('*.py')}|{'research/benchmark-lifecycle-dispatch.py','data/engine-effect-overrides.json'})
def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
before=hashes();prepared_emit=Catalog.emit
body=body_for(['리타','크라운','앨리스','마스트 : 로망틱 메이드','모더니아'],30,True)
body.update(seed=12345,burst_gauge_mode='fixed')
keys=('total_damage','members','base_stats','burst_timeline')
def execute(callback):
    with patch.object(Catalog,'emit',callback):
        start=time.perf_counter();value=a.evaluate(body);elapsed=(time.perf_counter()-start)*1000
    return elapsed,{key:value[key] for key in keys}
_,reference=execute(prepared_emit);execute(scanning_emit)
rows=[]
for pair in range(6):
    for label,callback in ([('scan',scanning_emit),('prepared',prepared_emit)] if pair%2==0 else [('prepared',prepared_emit),('scan',scanning_emit)]):
        ms,value=execute(callback);assert value==reference
        rows.append(dict(pair=pair,mode=label,wall_ms=ms))
assert before==hashes() and Catalog.emit is prepared_emit
medians={label:statistics.median(r['wall_ms'] for r in rows if r['mode']==label) for label in ('scan','prepared')}
report=dict(passed=True,cpu_battle=True,pairs=6,results_equal=True,medians_ms=medians,speedup=medians['scan']/medians['prepared'],samples=rows,
    source_sha256=before,scope='Same30s grown squad, alternating paired CPU evaluations. Only phase dispatch scanning is restored in control. Does not measure GPU kernel acceleration or all squad workloads.')
(ROOT/'research/typed-impacts-dispatch-performance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({key:report[key] for key in ('passed','pairs','medians_ms','speedup')}))
