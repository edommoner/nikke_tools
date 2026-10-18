"""Definition-index proof deduplicates trigger layouts, not battle results."""
import argparse,copy,hashlib,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from event_index_specs import build_index,EVENT_COUNT,TRIGGER_BASE,TRIGGER_WIDTH
from gpu_selector import Cuda
import detail_gpu as g

def inventory():
    unique={};accepted=[];rejected=[];standards=0
    for name,data in a.META.items():
        if not isinstance(data,dict) or name.startswith(('_','test_')) or a.spec.is_preview(name):continue
        names=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4]
        for stage in range(4):
            body=body_for(names,8);body['profile']['chars'][name]['favorite_stage']=stage
            try:compiled=a.evaluate({**body,'_compile_gpu_detail':True})
            except (ValueError,SystemExit) as error:
                rejected.append(dict(character=name,favorite=stage,error=str(error)));continue
            rows=compiled['program']['effects'];plan=build_index(rows)
            # Independent ordered full scan. Same row appears once per event;
            # matching descriptor multiplicity remains in the existing FSM.
            for event in range(EVENT_COUNT):
                expected=tuple(index for index,row in enumerate(rows) if any(row[TRIGGER_BASE+at*TRIGGER_WIDTH]==event for at in range(int(row[144]))))
                assert plan['definitions'][plan['offsets'][event]:plan['offsets'][event+1]]==expected
            signature=tuple(tuple(int(row[TRIGGER_BASE+at*TRIGGER_WIDTH]) for at in range(int(row[144]))) for row in rows)
            accepted.append(dict(character=name,favorite=stage,layout=len(unique) if signature not in unique else unique[signature]['index']))
            if signature not in unique:unique[signature]=dict(index=len(unique),compiled=compiled,plan=plan,character=name,favorite=stage)
            standards+=int(stage==0)
    assert standards==sum(row['favorite']==0 for row in accepted) and standards>0
    layouts=list(unique.values());real_count=len(layouts)
    for duplicate in (False,True):
        compiled=copy.deepcopy(layouts[0]['compiled']);rows=[]
        for index in range(g.NE):
            row=[0.0]*g.EW;row[1]=-1;row[57]=-1;row[144]=8
            for at in range(8):
                event=index%128 if duplicate else (index*8+at)%128
                descriptor=[event,1,0,-1,0,0,0]
                if event==49:descriptor=[49,1,1,0,0,0,1]
                if event==50:descriptor=[50,0,0,0,0,0,-1]
                row[TRIGGER_BASE+at*TRIGGER_WIDTH:TRIGGER_BASE+(at+1)*TRIGGER_WIDTH]=descriptor
            rows.append(row)
        compiled['program']['effects']=rows;compiled['program']['counter_single_body']=False
        plan=build_index(rows);assert len(plan['definitions'])==(256 if duplicate else 2048)
        layouts.append(dict(index=len(layouts),compiled=compiled,plan=plan,character='synthetic-duplicate-bound' if duplicate else 'synthetic-capacity-bound',favorite=0))
    return dict(accepted=accepted,rejected=rejected,standard_supported=standards,layouts=layouts,real_layouts=real_count)

def gpu_layouts(device,items,backend):
    total=0;entries=0
    for start in range(0,len(items),16):
        chunk=items[start:start+16];script=[];positions=[]
        for event in range(EVENT_COUNT):
            maximum=max(item['plan']['offsets'][event+1]-item['plan']['offsets'][event] for item in chunk)
            for page in range(max(1,math.ceil(maximum/(g.OW-4)))):
                positions.append((event,page));script.append([0,2,128,0,event,len(script),page,0])
        result=g.run(device,[item['compiled']['program'] for item in chunk],script,
            [item['compiled']['enemy'] for item in chunk],[item['compiled']['base_stats'] for item in chunk],module_backend=backend)
        for item,queries in zip(chunk,result['queries']):
            plan=item['plan'];entries+=len(plan['definitions'])
            for (event,page),row in zip(positions,queries):
                begin,end=plan['offsets'][event:event+2];offset=begin+page*(g.OW-4)
                expected=list(plan['definitions'][offset:min(end,offset+g.OW-4)]) if offset<end else []
                assert row[:4]==[begin,end,len(plan['definitions']),end-begin],(item['character'],event,page,row[:4])
                assert row[4:4+len(expected)]==expected,(item['character'],event,page,expected,row)
                assert not any(row[4+len(expected):]),(item['character'],event,page,row)
            total+=1
        assert all(not any(values) for values in result['totals']),'Index inspection must not execute attacks'
        print(json.dumps(dict(layouts_checked=total,total=len(items))),flush=True)
    return dict(layouts=total,entries=entries)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--backend',choices=('native','ptx'),default='native');parser.add_argument('--cpu-only',action='store_true');args=parser.parse_args()
    files=sorted({str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'app').glob('*.py')}|{'app/detail_effects.cu','data/engine-effect-overrides.json','scripts/verify-event-index-detail.py','scripts/detail_coverage.py'})
    if not args.cpu_only:files+=['app/detail_effects-sm86.cubin','app/detail_effects-sm86.json'] if args.backend=='native' else ['app/detail_effects.ptx','app/detail_effects-build.json']
    def hashes():return {p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
    before=hashes();started=time.perf_counter();proof=inventory();gpu=None
    if not args.cpu_only:
        device=Cuda()
        try:gpu=gpu_layouts(device,proof['layouts'],args.backend)
        finally:device.close()
    assert before==hashes()
    report=dict(passed=True,standard_supported=proof['standard_supported'],accepted_contexts=len(proof['accepted']),
        distinct_layouts=len(proof['layouts']),real_layouts=proof['real_layouts'],synthetic_layouts=2,accepted=proof['accepted'],rejected=proof['rejected'],gpu=gpu,
        source_sha256=before,source_stable=True,seconds=time.perf_counter()-started,
        scope='Ordered event-definition index only; each distinct trigger layout probed once. No new character acceptance, damage/game correctness or full battle-matrix claim.')
    suffix='cpu' if args.cpu_only else args.backend
    (ROOT/f'research/event-index-layouts-{suffix}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('passed','standard_supported','accepted_contexts','distinct_layouts','seconds')}),flush=True)

if __name__=='__main__':main()
