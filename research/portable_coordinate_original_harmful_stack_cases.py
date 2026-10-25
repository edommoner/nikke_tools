"""Unmodified original auto bodies, including the actual third full burst."""
import importlib.util
from pathlib import Path
def fixtures():
    s=importlib.util.spec_from_file_location('original_harmful_stack_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));f=importlib.util.module_from_spec(s);s.loader.exec_module(f)
    names=['도라','앵커 : 이노센트 메이드','드레이크','마스트 : 로망틱 메이드','N102']
    return [dict(name='coordinate-original-harmful-stack/Anchor/'+label,body=dict(f.body_for(names,duration),burst_gauge_mode='accumulate',seed=3901),coord=dict(auto_aim=[0.,0.],pierce_px=10.,explosion_scale=1.),patterns=[dict(id='world',kind='idle')],harmful_stack_witness=label) for label,duration in [('control',6),('third-full-burst',86)]]
