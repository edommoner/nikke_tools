"""Literal private stage inputs after canonical complete-profile preparation."""
import copy,math
from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def configured(body,stages,live_overrides=()):
    import engine_worker
    from calculator.buff_manager import BuffManager
    if not isinstance(stages,dict) or any(name not in body['squad'] or type(stage) is not str or stage not in ('1','2','3','A') for name,stage in stages.items()):raise ValueError('Expected literal member burst-stage overrides')
    for row in live_overrides:
        if set(row)!={'owner','stage','duration'} or row['owner'] not in body['squad'] or row['stage'] not in ('1','2','3','A') or type(row['duration']) not in (int,float) or not math.isfinite(row['duration']) or row['duration']!=-1 and row['duration']<=0:raise ValueError('Invalid literal live stage override')
    original=engine_worker.sim.prepare;original_init=BuffManager.__init__
    def prepare(request):
        run=original(request);run.squad=copy.deepcopy(run.squad)
        for char in run.squad:
            if char['name'] in stages:char['burst_stage']=stages[char['name']]
        return run
    def initialized(manager,*args,**kwargs):
        original_init(manager,*args,**kwargs)
        for i,row in enumerate(live_overrides):
            effect=dict(name='literal-stage-override-'+str(i),source='스킬1',type='buff',stat='burst_stage_override:'+row['stage'],target='self',fixed_value=0,duration=row['duration'],trigger=dict(timing=['battle_start'],condition=[]))
            manager._effects.append((effect,row['owner']))
        if live_overrides:manager._build_notify_index()
    with patch.object(engine_worker.sim,'prepare',prepare),patch.object(BuffManager,'__init__',initialized):yield
