"""Global team-hit counters and attacker attribution, independent CPU oracle."""
import argparse,copy,hashlib,importlib.util,json,math,random,sys
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'scripts')]
from detail_coverage import a,body_for
from calculator.buff_manager import BuffManager
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
oracle=load('team_hit_oracle','scripts/verify-detail.py')
p=load('team_hit_periodic','scripts/verify-periodic-detail.py')
raw=load('team_hit_injection','scripts/verify-cleanse-detail.py')
E=p.effect
oracle.EVENT={**oracle.EVENT,'squad_part_hit':44,'squad_body_hit':45}

@contextmanager
def manual_team_events():
    original=BuffManager.notify
    def route(self,event,t,caster,*args,**kwargs):
        if event in ('squad_part_hit','squad_body_hit'):return self.notify_team_hit(event,t,caster)
        return original(self,event,t,caster,*args,**kwargs)
    with patch.object(BuffManager,'notify',route):yield

def primitives():
    refs=json.loads((ROOT/'research/detail-team-hits-cpu-references.json').read_text(encoding='utf-8'))
    for i,ref in enumerate(refs['cases']):
        commands=[(0,0,j) for j in range(5)]
        for step,attacker in enumerate((1,2,1,4,2,3),1):
            t=step/10
            commands.append((t,44 if ref['event']=='squad_part_hit' else 45,attacker))
            commands.extend((t+.0001,'query',j) for j in range(5))
        commands.extend((2,'query',j) for j in range(5))
        yield 'reference-'+str(i),ref['chars'],ref['effects'],ref['base_stats'],commands
    names=refs['cases'][0]['chars'];names=copy.deepcopy(names)
    roster=[c['name'] for c in names];stats=refs['cases'][0]['base_stats']
    for condition in ([],['has_defender_ally'],['no_defender_ally'],['back_row'],['prob:50']):
        # Source is slot 1, so back_row is true even for a front-row attacker.
        source=roster[1]
        for target in ('self','allies_right:1','all_allies'):
            effect=E('shared team budget','buff','atk_pct',7,target,event='body_hit_count:1',condition=condition,max_trigger=3,max_stack=10,duration=1)
            commands=[(0,0,j) for j in range(5)]
            for k,attacker in enumerate((4,0,2,3,1,4,0),1):
                commands.append((k/10,45,attacker));commands.extend((k/10+.0001,'query',j) for j in range(5))
            yield 'budget-'+str(condition)+'-'+target,names,[(effect,source)],stats,commands
    for kind,stat in [('damage','bonus_damage'),('instant','current_hp_reduce')]:
        effect=E('team '+kind,kind,stat,3,'target_body' if kind=='damage' else 'self',event='part_hit_count:2',max_trigger=3)
        commands=[(0,0,j) for j in range(5)]
        for k,attacker in enumerate((1,3,2,4,2,0),1):
            commands.append((k/10,44,attacker));commands.extend((k/10+.0001,'query',j) for j in range(5))
        effects=[(effect,roster[0])]
        if kind=='instant':effects.append((E('HP witness','buff','atk_pct',9,'all_allies',event='passive',condition=['ally_hp_below:99']),roster[0]))
        yield 'kind-'+kind,names,effects,stats,commands


def bodies(quick=False):
    for subject in ('D : 킬러 와이프','루마니'):
        for world in (('none','live') if quick else ('none','legacy','live','clear')):
            for shooting in (('auto',) if quick else ('auto','character')):
                for mode in (('fixed',) if quick else ('fixed','accumulate')):
                    body=body_for([subject,'리타','크라운','앨리스','모더니아'],16 if quick else 20,True)
                    for i,c in enumerate(body['profile']['chars'].values()):c['skill_levels']={'1':3+i,'2':9-i,'3':3+i}
                    body.update(seed=12345,shooting_policy=shooting,burst_policy='rules',burst_gauge_mode=mode,_debug_random_state=True)
                    if shooting=='character':
                        body['profile']['chars']['베스티']=body['profile']['chars'].pop('모더니아')
                        body['squad'][3:]=['베스티','앨리스']
                    body['enemy']['core_px']=5
                    if world=='legacy':body['enemy']['has_parts']=True
                    if world=='live':body['enemy']['parts']=[dict(name='armor',hp=0,reach=1),dict(name='cannon',hp=300000,reach=2)]
                    extra={}
                    if world=='clear':
                        body['enemy']['parts']=[dict(name='a',hp=100000000,reach=1),dict(name='b',hp=100000000,reach=2)]
                        extra={'리타':[E('authored clear','damage','damage',1000000,'all_enemies',event='every:8s',max_trigger=1,hits_parts=True)]}
                    yield subject+'-'+world,body,world,extra
