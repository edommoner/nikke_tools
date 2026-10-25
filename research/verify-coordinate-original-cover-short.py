"""Original cover-revival definitions through the common battle/selection readers."""
import array,importlib.util,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'app'),str(ROOT/'research')]
s=importlib.util.spec_from_file_location('original_cover_parent',ROOT/'research/verify-coordinate-original-short.py');parent=importlib.util.module_from_spec(s);s.loader.exec_module(parent)
from portable_coordinate_original_cover_cases import fixtures
from portable_coordinate_original_cases import prepare_case
from world_original_cover_native import capture
suite=parent.suite;cross=parent.cross;SOURCE='gpu/world_coordinate_original_cover_entry.slang';INPUT_WORDS=parent.INPUT_WORDS;OUTPUT_WORDS=parent.OUTPUT_WORDS;STRICT_WIRE_DIMENSIONS=True
NATIVE_COMPARISON_CONTEXT=parent.NATIVE_COMPARISON_CONTEXT
compile_coordinate_battle=parent.compile_coordinate_battle

def prepare():
    rows=[]
    for row in fixtures():
        c,p=prepare_case(row);c['cover_witness']=row['cover_witness'];c['python_observers_only']=True;w,m,b,d=compile_coordinate_battle(p);rows.append((c['name'],w,(c,m,b,d)))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()

def verify_witness(case,n):
    observed=n['original_cover'];witness=case['cover_witness'];hits=n['battle']['hits'];deliveries=observed['deliveries'];names=case['names']
    assert observed['requests'] and all(case['effects'][r['row']]['stat']=='cover_revive' and r['owner']==0 for r in observed['requests'])
    assert len(hits)==witness['broken'] and all(h['cover']>0 for h in hits),'Declared real attacks must land on reload cover'
    assert len(deliveries)==witness['revived'],'The original burst must actually revive the expected number of covers'
    if witness['scenario']=='pool':assert max(sum(v<=0 for v in r['before']['current'].values()) for r in observed['requests'])==3,'Real sampling must choose from three broken covers'
    for d in deliveries:
        name=names[d['target']];assert d['before']['current'][name]==0 and d['hp']>0 and d['after']['current'][name]==d['hp']
        assert d['before']['maximum']==d['after']['maximum'],'Revival cannot change cover capacity'
        assert all(d['before']['current'][other]==value for other,value in d['after']['current'].items() if other!=name),'Only the selected cover may be revived'
    return True

def native_reference(domain):
    with capture(domain[0]) as observed:n=parent.native_reference(domain)
    n['original_cover']=observed;verify_witness(domain[0],n);return n

def compare(block,domain):
    from world_coordinate_sampled_skill_native import creation_indices
    from portable_runtime import decode
    with creation_indices(domain[0]) as indices:n=native_reference(domain)
    parent.compare_observed(block,domain,n,indices)
    actual=decode(block[:159744],domain[1]);c=domain[0]
    for carrier in actual['carriers']:
        source=domain[1]['binding_source_indices'][carrier['definition']];effect=c['effects'][source]
        if carrier['active'] and effect.get('stat')=='atk_caster_based_pct' and effect.get('target','').startswith('allies_random:'):
            assert carrier['lazy_pending'],'A diagnostic snapshot must not freeze original late random numeric membership'
    for index,source in enumerate(domain[1]['binding_source_indices']):
        if c['effects'][source].get('stat')=='cover_revive':assert actual['timers'][index]['activations']==sum(r['row']==source for r in n['original_cover']['requests']),'Every original cover revival request must execute'
    assert [r['hp'] for r in n['battle']['covers']]==[n['original_cover']['final']['current'][name] for name in c['names']],'Final stored cover observations must agree'
    return n

def validate_rejection(block,name):raise AssertionError('Original cover definitions cannot be discarded')
