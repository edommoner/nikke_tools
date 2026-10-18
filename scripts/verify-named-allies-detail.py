"""Existing masked-ally executor: independent recipient table and real skill usage."""
import argparse,copy,hashlib,importlib.util,json,sys,time
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/d) for d in ('app','scripts','tests')]
from detail_coverage import a,body_for
from test_named_ally_targets import TARGET,BASE,characters,effect
from calculator.buff_manager import BuffManager
from gpu_selector import Cuda
import detail_gpu as g
spec=importlib.util.spec_from_file_location('named_allies_full',ROOT/'scripts/verify-extended-detail.py');full=importlib.util.module_from_spec(spec);spec.loader.exec_module(full)

def quantities(device,backend):
    programs=[];stats=[];expected=[];cpu_rows=[];labels=[]
    for slot in (*range(5),None):
        names=BASE.copy() if slot is None else BASE[:4].copy();
        if slot is not None:names.insert(slot,TARGET)
        chars=characters(names);es=[(effect(TARGET),names[0]),(effect(TARGET,7,'on_attack'),names[0])]
        programs.append(g.compile_effects(chars,es));bs={n:dict(atk=1000,hp=1000000,**{'def':0}) for n in names};stats.append(bs)
        class BM(BuffManager):
            def _register_all(self):self._effects=copy.deepcopy(es);self._build_notify_index()
        bm=BM(chars,state=dict(base_stats=bs,enemy={'def':0},full_burst=False));actual=[];wanted=[]
        for at,event,amount in ((0,'battle_start',25),(.1,'on_attack',32),(.21,None,7),(.31,None,0)):
            bm.tick(at)
            if event:bm.notify(event,at,names[0])
            actual += [bm.get_buffs(n,'__enemy__',at).get('atk_pct',0) for n in names]
            wanted += [amount if i==slot else 0 for i in range(5)]
        assert actual==wanted,(slot,actual,wanted)
        cpu_rows.append(actual);expected.append(wanted);labels.append('absent' if slot is None else 'slot'+str(slot+1))
    script=[]
    for at,event in ((0,0),(.1,7),(.21,None),(.31,None)):
        script.append([at,0 if event is not None else 1,event or 0,0,0,-1,0,0])
        for who in range(5):script.append([at,2,103,who,0,sum(r[1]==2 for r in script),0,0])
    result=g.run(device,programs,script,[[0,0]]*len(programs),stats,module_backend=backend)
    gpu_rows=[[q[0] for q in squad] for squad in result['queries']];assert gpu_rows==expected,(gpu_rows,expected)
    return [dict(name='exact-recipient-slots-and-expiry',passed=True,recipient_cases=labels,cpu=cpu_rows,gpu=gpu_rows,independent_expected=expected,batch_squads=6)]

def squads(device,backend):
    rows=[]
    for present in (True,False):
        names=['아비스타',TARGET if present else '리타','크라운','앨리스','모더니아'];body=body_for(names,90,True);body.update(seed=12345,burst_gauge_mode='fixed')
        compiled=a.evaluate({**body,'_compile_gpu_detail':True});program=compiled['program'];labels={v:k for k,v in program['states'].items()}
        named={labels[int(row[3])] for row in program['effects'] if int(row[0])==0 and row[4]==8 and row[48]==(2 if present else 0)}
        # Require actual raw named-target effects, not arbitrary equipment masks.
        reference=BuffManager(compiled['prepared'].squad)
        wanted={e['name'] for e,owner in reference._effects if owner==names[0] and e.get('target')==TARGET};assert len(wanted)==3 and wanted<=named
        seen=set();original=BuffManager._activate
        def observe(self,e,caster,t,*args,**kwargs):
            result=original(self,e,caster,t,*args,**kwargs)
            if caster==names[0] and e.get('target')==TARGET:
                if any(ab.effect is e and TARGET in (ab.target_chars or []) and ab.expires_at>t for ab in self._active):seen.add(e['name'])
            return result
        with patch.object(BuffManager,'_activate',observe):row=full.compare(device,'raw-named-ally-'+('present' if present else 'absent'),body,module_backend=backend)
        assert row['passed'],row
        assert seen==wanted if present else not seen,(present,seen,wanted)
        row.update(raw_skills_retained=True,named_effects_exercised=sorted(seen),named_effects_expected=sorted(wanted),named_recipient_present=present)
        rows.append(row);print(json.dumps(dict(name=row['name'],passed=True,cpu=row['cpu_total'],gpu=row['gpu_total'],named_activations=len(seen))),flush=True)
    return rows

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--backend',choices=('native','ptx'),default='native');args=ap.parse_args()
    files=list((ROOT/'app').glob('*.py'))+list((ROOT/'scripts').glob('*.py'))+[ROOT/'tests/test_named_ally_targets.py',ROOT/'app/detail_effects.cu']
    files += [ROOT/'app'/name for name in (('detail_effects-sm86.cubin','detail_effects-sm86.json') if args.backend=='native' else ('detail_effects.ptx','detail_effects-build.json'))]
    before={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in files};started=time.perf_counter();device=Cuda()
    try:rows=quantities(device,args.backend)+squads(device,args.backend)
    finally:device.close()
    assert before=={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in before}
    report=dict(passed=True,cases=rows,source_stable=True,source_sha256=before,cpu_trace_used_as_gpu_input=False,seconds=time.perf_counter()-started,
        scope='Exact named-ally conversion to existing target mask; six independent recipient/expiry stimuli and two raw90s squads. No new GPU state or arithmetic.')
    (ROOT/f'research/named-allies-{args.backend}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':main()
