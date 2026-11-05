"""Complete original Trina profiles with zero/one/two eligible AR allies."""
import importlib.util
from pathlib import Path

def fixtures():
    s=importlib.util.spec_from_file_location('leftmost_real_factory',Path(__file__).with_name('verify-world-projectile-rosters.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
    rows=[]
    configs=[('empty',m.policy.roster_for('트리나'),[]),('two',['트리나','홍련','드레이크','N102','솔져 E.G.'],[1]),('last',['트리나','미란다','드레이크','N102','홍련'],[4])]
    for label,names,picked in configs:
        for duration in (3,30):
            body=dict(m.body_for(names,duration),burst_gauge_mode='accumulate')
            rows.append(dict(name='leftmost-real/'+label+'/'+str(duration)+'s',body=body,contract=dict(picked=picked)))
    return rows
