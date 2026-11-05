"""Definition-index proof deduplicates trigger layouts, not battle results."""
import argparse,copy,hashlib,json,math,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from event_index_specs import build_index,EVENT_COUNT,TRIGGER_BASE,TRIGGER_WIDTH
import detail_gpu as g

def inventory():
    unique={};accepted=[];rejected=[];standards=0
    for name,data in a.META.items():
        if not isinstance(data,dict) or name.startswith(('_','test_')) or a.spec.is_preview(name):continue
        names=[name]+[n for n in ['모더니아','루주','마스트 : 로망틱 메이드','도라','얀'] if n!=name][:4]
        for stage in range(4):
            body=body_for(names,8);body['profile']['chars'][name]['favorite_stage']=stage
            try:compiled=a.evaluate({**body,'_compile_detail':True})
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



if __name__=='__main__':main()
