"""Same original seven battles; shared full arena comparison plus allocation banks."""
import array,copy,importlib.util,json,struct,sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research')]
spec=importlib.util.spec_from_file_location('weighted_original_comparison',ROOT/'research/verify-original-catalogue.py');base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
from portable_weighted_battle_wire import INPUT,OUTPUT,LAYOUT,SOURCE,compile_weighted
from portable_weighted_battle_cases import fixtures
from portable_weighted_cover_condition_cases import fixtures as positive_cover_cases
from portable_original_catalogue_cases import selected_rows,prepare as original_prepare
from weighted_incoming_battle_model import weighted_incoming
suite=SimpleNamespace(INPUT=INPUT,OUTPUT=OUTPUT);cross=base.cross
STRICT_WIRE_DIMENSIONS=True;NATIVE_COMPARISON_CONTEXT=base.NATIVE_COMPARISON_CONTEXT
def prepare():
    rows=[];template=selected_rows(['original-catalogue/hp-shield/베이/favorite-0/30s'])[0]
    for raw in fixtures()+positive_cover_cases():
        row=copy.deepcopy(template);row.update(name=raw['name'],body=copy.deepcopy(raw['body']),patterns=copy.deepcopy(raw['patterns']),allocation=copy.deepcopy(raw['allocation']))
        # Original contracts have no intercepting enemy shield. Typed automatic
        # aim can select a live target at any geometry, so its audit-only node
        # must remain unspawned for the entire battle, not merely be far away.
        duration=raw['body']['duration'];node='weighted-audit-unspawned'
        row['patterns'].append(dict(id=node,kind='idle',delay=duration+1,until=dict(time=duration+2)))
        row['body']['enemy']['patterns']=copy.deepcopy(row['patterns'])
        row['typed_bindings'][0]['node']=node
        row['typed_geometry']['shapes']=[dict(x=1000000.,y=1000000.,r=1.,z=1.)]
        row['catalogue_profile'].update(favorite_stage=raw['contract']['favorite_stage'],duration=raw['body']['duration'])
        if raw.get('declared_burst_sequence'):row['declared_burst_sequence']=copy.deepcopy(raw['declared_burst_sequence'])
        c,p=original_prepare(row);c['weighted_case']=copy.deepcopy(raw)
        w,m,b,d=compile_weighted(p,row);rows.append((c['name'],w,(c,m,b,d)))
    seed=rows[0][1]
    for label,at,value in [('magic',0,0),('version',1,2),('owners',2,4),('reserved',3,1),('zero-weight',5,0),('negative-weight',7,0xbff00000),('nan-weight',9,0x7ff80000),('tail',15,1),('source-row-zero',10,0),('source-row-collision',11,seed[LAYOUT['BASE']+10]),('source-row-overflow',10,513)]:
        w=list(seed);w[LAYOUT['BASE']+at]=value
        if label=='zero-weight':w[LAYOUT['BASE']+4]=0
        rows.append(('reject/weighted-battle/'+label,w,None))
    from portable_specs import LIMITS as L
    condition_source=rows[7][2][0]
    condition_row=next(i for i,e in enumerate(condition_source['effects']) if condition_source['owners'][i]==0 and e.get('stat')=='heal_hp_pct' and e.get('trigger',{}).get('condition')==['not_self_cover_alive'])
    for label,offset,value in [('cover-condition-reserved',1,1),('cover-condition-nan',3,0x7ff80000)]:
        w=list(rows[7][1]);w[L['CONDITION_BASE']+condition_row*L['CONDITION_WORDS']+offset]=value
        rows.append(('reject/weighted-battle/'+label,w,None))
    raw=array.array('I',[len(rows)])
    for _,w,_ in rows:raw.extend(w)
    if sys.byteorder!='little':raw.byteswap()
    return rows,raw.tobytes()
_original_native=base.native_reference
def native_reference(domain):
    c=domain[0];raw=c['weighted_case']
    from contextlib import nullcontext
    from world_weighted_cover_condition_native import capture
    positive='/broken-cover-condition/' in raw['name']
    with (capture() if positive else nullcontext()) as heals:
        with weighted_incoming(raw['allocation'],raw['names']) as data:n=_original_native(domain)
    if n['coordinate_typed_weapon']['attacks']:raise AssertionError('Audit-only typed target intercepted an original body shot')
    # Same incoming contract as the already verified native-only CLI. The typed
    # arena adds full weapon/skill/actor observations, never a new damage oracle.
    saved=json.loads((ROOT/'tests/fixtures/weighted-battle-cpu-v1.json').read_text())
    if positive:saved=json.loads((ROOT/'tests/fixtures/weighted-cover-condition-cpu-v1.json').read_text())
    previous=next(r['native'] for r in saved['cases'] if r['name']==raw['name'])
    if data!=previous['weighted_incoming'] or n['battle']['hits']!=previous['hits']:raise AssertionError('Original seven-battle incoming contract changed in full arena')
    if positive:
        if heals!=previous['conditional_heals']:raise AssertionError('Original positive cover-heal contract changed in full arena')
        n['conditional_heals']=heals
    n['weighted_incoming']=data;return n
def compare_banks(block,domain,native):
    from portable_weighted_battle_wire import MAGIC
    head=LAYOUT['OUTPUT_BASE'];data=native['weighted_incoming'];snaps=data['snapshots'];receipts=data['cover_receipts'];c,m=domain[:2]
    assert list(block[head:head+3])==[MAGIC,len(snaps),len(receipts)]
    assert not any(block[head+3:head+LAYOUT['SNAPSHOTS']]),'Header padding and every completed frame scratch must be zero'
    def number(at,value):assert list(block[at:at+2])==list(struct.unpack('<II',struct.pack('<d',value))),(at,value,list(block[at:at+2]))
    markers=c['weighted_case']['contract']['original_markers'];body=next(r['row'] for r in markers if r['effect']['target']=='all_allies');cover=next(r['row'] for r in markers if r['effect']['target']=='self_cover')
    for i,s in enumerate(snaps):
        at=head+LAYOUT['SNAPSHOTS']+i*48
        assert list(block[at:at+4])==[s['body_mask'],c['names'].index(s['caster']),c['names'].index(s['struck']),s['active_mask']]
        for off,key in [(4,'time'),(6,'amount'),(8,'total'),(24,'body_source_activated_at')]:number(at+off,s[key])
        for who,value in enumerate(s['shares']):number(at+10+who*2,value)
        assert list(block[at+22:at+24])==[m['binding_source_indices'].index(body),m['binding_source_indices'].index(cover)+1 if s['active_mask']&32 else 0]
        assert not any(block[at+26:at+48])
    assert not any(block[head+LAYOUT['SNAPSHOTS']+len(snaps)*48:head+LAYOUT['RECEIPTS']])
    for i,r in enumerate(receipts):
        at=head+LAYOUT['RECEIPTS']+i*32
        assert list(block[at:at+2])==[r['snapshot'],int(r['delivered'])]
        for off,key in [(2,'time'),(4,'hp_before'),(6,'applied'),(8,'hp_after')]:number(at+off,r[key])
        assert not any(block[at+10:at+32])
    assert not any(block[head+LAYOUT['RECEIPTS']+len(receipts)*32:])
def compare(block,domain):
    with patch.object(base,'native_reference',native_reference):native=base.compare(block[:LAYOUT['OUTPUT_BASE']],domain)
    compare_banks(block,domain,native)
    if 'conditional_heals' in native:
        from portable_runtime import decode
        c,m=domain[:2];rows=[i for i,e in enumerate(c['effects']) if c['owners'][i]==0 and e.get('stat')=='heal_hp_pct' and e.get('trigger',{}).get('condition')==['not_self_cover_alive']]
        assert len(rows)==1
        assert decode(block[:159744],m)['timers'][m['binding_source_indices'].index(rows[0])]['activations']==len(native['conditional_heals'])
    return native
def validate_rejection(block,name):assert name.startswith('reject/weighted-battle/') and block[0]==64
