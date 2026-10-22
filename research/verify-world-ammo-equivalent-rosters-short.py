"""Complete ammo-equivalent profile; unchanged real-battle oracle."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('heal_real_roster',ROOT/'research/verify-world-roster-regression-short.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
suite,cross=base.suite,base.cross
PROFILES=('신데렐라 : 크리스탈 웨이브',)
DURATIONS=(3,30)
def prepare():
    entries=[]
    for character in PROFILES:
        for duration in DURATIONS:
            body=dict(base.real.body_for(base.real.policy.roster_for(character),duration),burst_gauge_mode='accumulate')
            body['profile']['chars'][character]['favorite_stage']=0
            prepared=base.real.engine_worker.evaluate(dict(body,_portable_static_inputs=True))
            words,metadata=base.real.compile_projectile_battle(prepared)
            case=dict(character=character,favorite_stage=0,duration=duration,body=body)
            entries.append((f'real/{character}/favorite-0/{duration}s',words,(case,prepared,words,metadata)))
    packed=array.array('I',[len(entries)])
    for _,words,_ in entries:packed.extend(words)
    if sys.byteorder!='little':packed.byteswap()
    return entries,packed.tobytes()
compare=base.compare
