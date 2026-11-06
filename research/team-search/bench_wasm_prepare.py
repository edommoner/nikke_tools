"""Prepare exact parity/S9 browser plans without CPU evaluation; stream readbacks.

--mode identity: all S1 rows, soft/hard byte comparison and >=256 stratified native checks.
--mode benchmark: first 256 native-success S9 rows with S1 settings, compare then
balanced A/B/B/A for each of 1 and 10 workers. Only owned temporary inputs cleaned.
Use an external free-space guard; this helper also checks the 20.5 GiB floor.
"""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'app'))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--mode',choices=('identity','benchmark'),required=True)
    p.add_argument('--scratch',type=Path,required=True)
    a=p.parse_args();a.scratch.mkdir(parents=True,exist_ok=True)
    import parity_gate as gate
    import portable_detail as detail
    import portable_native as native
    import portable_wasm as wasm
    import portable_slang_generation as generation
    def forbid(*args,**kwargs):raise RuntimeError('CPU reference execution forbidden')
    # Preparation stops at the existing evaluator yield. Admission failures are
    # returned as unsupported records; no fallback or finish/decode runs.
    evaluate=detail.engine_worker.evaluate
    def static_only(body):
        if body.get('_portable_static_inputs') is not True:forbid()
        return evaluate(body)
    detail.engine_worker.evaluate=static_only
    detail.cpu_fallback_portable_detail=forbid
    detail._cpu_fallback=lambda body,folder,record,**kw:dict(unsupported=record['unsupported'])
    corpus=gate.load_corpus(ROOT/'research/parity/s1-corpus.json')
    if a.mode=='identity':rows=corpus['squads']
    else:
        settings=json.loads((ROOT/'research/team-search/s1-inputs.json').read_text())
        body=dict(corpus['base']);body.update(settings['settings'])
        rows=[]
        for line in (ROOT/'research/team-search/s9-dataset.jsonl').open():
            r=json.loads(line)
            if r['backend']=='native_detail':rows.append(dict(r,body=dict(body,squad=r['members'])))
            if len(rows)==256:break
        if len(rows)!=256:raise RuntimeError('Need 256 native-success S9 rows')
    builds={};prepared=[];unsupported=[]
    with tempfile.TemporaryDirectory(prefix='wasm-inputs-',dir=a.scratch) as tmp:
        tmp=Path(tmp)
        for row in rows:
            if shutil.disk_usage(tmp).free<int(20.5*1024**3):raise RuntimeError('20.5 GiB storage floor')
            with tempfile.TemporaryDirectory(prefix='prepare-',dir=tmp) as capture:
                os.environ['NIKKE_DETAIL_CAPTURE_ROOT']=capture
                body=dict(row['body'],compute_backend='browser_detail')
                g=detail._evaluation(body,verification='deferred')
                try:
                    try:plan=next(g)
                    except StopIteration as done:
                        unsupported.append(dict(id=row['id'],status='unsupported',soft=done.value,hard=done.value));continue
                    source=plan['source']
                    if source not in builds:
                        soft,hashes=generation.build(ROOT,source,'portableEvents',target='cpp')
                        soft_wasm,soft_receipt=wasm.build_wasm(ROOT,soft['cpp'])
                        hard_wasm,hard_receipt=wasm.build_product(ROOT,source)
                        host,host_receipt=native.build_host(ROOT,soft['cpp'])
                        if soft_receipt['identity']==hard_receipt['identity']:raise AssertionError('variant identity unchanged')
                        builds[source]=dict(soft=str(soft_wasm),hard=str(hard_wasm),host=str(host),
                            soft_receipt=soft_receipt,hard_receipt=hard_receipt,native_receipt=host_receipt)
                    b=builds[source];inp=tmp/f"{row['id']}.bin.gz";inp.write_bytes(gzip.compress(plan['packed'],mtime=0))
                    prepared.append(dict(id=row['id'],status='prepared',source=source,input=str(inp),
                        input_words=plan['input_words'],output_words=plan['output_words'],input_sha256=hashlib.sha256(plan['packed']).hexdigest(),
                        soft=b['soft'],hard=b['hard'],members=row['members']))
                finally:g.close()
            if len(prepared)%128==0:print(json.dumps(dict(prepared=len(prepared),unsupported=len(unsupported))),flush=True)
        if not prepared:raise RuntimeError('No prepared rows: '+str(unsupported[:1]))
        if a.mode=='benchmark' and unsupported:raise RuntimeError('Benchmark requires all 256 rows; unsupported='+str(unsupported))
        selected=set()
        if a.mode=='identity':
            by_source=defaultdict(list)
            for r in prepared:by_source[r['source']].append(r)
            # Every source family, smallest/largest layouts, largest-output rows,
            # known mismatches, then evenly distributed corpus positions.
            selected.update(r['id'] for r in prepared if r['id'] in (606,836))
            for group in by_source.values():
                group.sort(key=lambda r:(r['output_words'],r['id']))
                selected.update(group[i]['id'] for i in (0,len(group)//2,len(group)-1))
            selected.update(r['id'] for r in sorted(prepared,key=lambda r:r['output_words'],reverse=True)[:32])
            for i in range(256):selected.add(prepared[i*(len(prepared)-1)//255]['id'])
            # Keep all strata even if this yields more than 256 rows.
            for r in prepared:
                if r['id'] in selected:r.update(native=builds[r['source']]['host'],native_python=sys.executable)
        manifest=tmp/'manifest.json';manifest.write_text(json.dumps(dict(rows=prepared)))
        evidence=a.scratch/(a.mode+'-rows.jsonl')
        if evidence.exists():raise RuntimeError('Refuse to overwrite evidence: '+str(evidence))
        with evidence.open('w') as f:
            for r in unsupported:f.write(json.dumps(r,ensure_ascii=False)+'\n')
        def run(variant,workers):
            command=['node',str(ROOT/'research/team-search/bench_wasm.mjs'),'--manifest',str(manifest),'--workers',str(workers),'--variant',variant]
            if variant=='compare':command+=['--evidence',str(evidence)]
            result=subprocess.run(command,check=True,capture_output=True,text=True)
            if result.stderr:print(result.stderr,file=sys.stderr)
            report=json.loads(result.stdout);print(json.dumps(report),flush=True);return report
        reports=[run('compare',10)]
        if a.mode=='benchmark':
            expected={r['id']:r['hard']['sha256'] for r in map(json.loads,evidence.read_text().splitlines()) if r['status']=='identical'}
            if len(expected)!=256:raise RuntimeError('S9 byte identity incomplete')
            for r in prepared:r['expected_sha256']=expected[r['id']]
            manifest.write_text(json.dumps(dict(rows=prepared)))
            for workers in (1,10):
                for variant in ('soft','hard','hard','soft'):reports.append(run(variant,workers))
        summary=dict(mode=a.mode,requested=len(rows),prepared=len(prepared),unsupported=unsupported,native_selected=sorted(selected),
            strata=[dict(source=s,rows=len([r for r in prepared if r['source']==s]),
                max_output_bytes=max(r['output_words']*4 for r in prepared if r['source']==s),
                native_ids=[r['id'] for r in prepared if r['source']==s and r['id'] in selected]) for s in builds],
            builds=builds,reports=reports,temporary_input_bytes=sum(Path(r['input']).stat().st_size for r in prepared))
        (a.scratch/(a.mode+'-summary.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':main()
