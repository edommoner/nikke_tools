"""Actual full native battle vs shared battle/typed Frame, with no second clock."""
import array,copy,importlib.util,struct,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/p) for p in ('app','research','scripts')]
import engine_worker
from destructible_battle_cases import fixtures
from destructible_battle_runtime import typed_battle
from destructible_skill_specs import coefficient
from world_authored_roster import skill_levels
from destructible_world_runtime import compile_bindings
from world_frame_native import observe,roster_names
from portable_specs import LIMITS as L
s=importlib.util.spec_from_file_location('typed_battle_base',ROOT/'research/verify-world-projectile.py');base=importlib.util.module_from_spec(s);s.loader.exec_module(base)
s=importlib.util.spec_from_file_location('typed_battle_digest',ROOT/'research/summarize-portable-cross-gpu.py');cross=importlib.util.module_from_spec(s);s.loader.exec_module(cross)
suite=types.SimpleNamespace(INPUT=109536,OUTPUT=1048576)
def number(block,at):return struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
def compile_case(c):
    typed=[i for i,e in enumerate(c['effects']) if e.get('target')=='all_projectiles']
    if len(typed)!=1:raise ValueError('One plain typed definition required')
    lowered=copy.deepcopy(c);lowered['effects'][typed[0]]['target']='boss'
    w,m,b=base.compile_case(lowered)
    row=m['binding_source_indices'].index(typed[0])
    nodes=[dict(id=p['id']) for p in c['patterns']];_,_,bindings=compile_bindings(nodes,c['typed_bindings'])
    extra=[0]*5136;extra[2320]=len(bindings)
    for i,r in enumerate(bindings):
        at=2328+i*12;owner=[0xffffffff,0,0] if r.owner is None else [int(r.owner.kind),r.owner.identity,r.owner.generation]
        extra[at:at+8]=[r.node,int(r.handle.kind),r.handle.identity,*struct.unpack('<II',struct.pack('<d',r.capacity)),*owner]
    extra[5120:5124]=[row,c['max_attacks'],1,0x44425431]
    w.extend(extra);assert len(w)==suite.INPUT
    return w,(c,m,b)
def prepare():
    rows=[];counter_rows=[];reentrant_rows=[];context_rows=[]
    for c in fixtures():
        w,domain=compile_case(c);(context_rows if c.get('context_contract') else reentrant_rows if c.get('reentrant_contract') else counter_rows if c.get('counter_contract') else rows).append((c['name'],w,domain))
    seed=rows[0][1]
    for label,offset,value in [('row',109520,256),('capacity-zero',109521,0),('capacity-overflow',109521,129),('context-policy',109522,0),('magic',109523,0),('reserved',109524,1),('second-clock',104400,0x57533031),('binding-node',104400+2328,32),('binding-capacity',104400+2332,0x7ff80000),('binding-reserved',104400+2336,1)]:
        w=list(seed);w[offset]=value;rows.append(('reject/destructible-battle/'+label,w,None))
    coexist=next(w for n,w,c in rows if n.endswith('/ordinary-part-clear-opens-typed'))
    w=list(coexist);w[104400+2328]=0;rows.append(('reject/destructible-battle/typed-binding-to-canonical-clear',w,None))
    rows.extend(counter_rows)
    counter=next(c for c in fixtures() if c.get('counter_contract')=='live-threshold')
    for label,change in [('unmodelled-target-state',dict(condition=['target_state:marker'])),('unmodelled-target-field',dict(target='target',stat='def_pct'))]:
        c=copy.deepcopy(counter)
        if 'condition' in change:c['effects'][1]['trigger']['condition']=change['condition']
        else:c['effects'][1].update(change)
        w,_=compile_case(c);rows.append(('reject/destructible-battle/'+label,w,None))
    rows.extend(reentrant_rows)
    rows.extend(context_rows)
    packed=array.array('I',[len(rows)])
    for _,w,_ in rows:packed.extend(w)
    if sys.byteorder!='little':packed.byteswap()
    return rows,packed.tobytes()
def native_reference(domain):
    c,m,b=domain;names=roster_names(c)
    with typed_battle(c['typed_bindings'],max_attacks=c['max_attacks']) as data:n=observe(c)
    from effect_runtime import state
    assert len(data['managers'])==1
    runtime=state(data['managers'][0]);assert not runtime.event_stack and not runtime.impact_stack and not runtime.activation_stack,'Native typed context leaked'
    if c.get('observe_target_counters'):
        # Same full-counter comparison contract as verify-world-counter-landings:
        # notification profiling is a CPU-only observation; exact completions,
        # resources/epochs, packets, death set and resulting battle stay compared.
        n['target_counters'].pop('events')
    world=data['worlds'][0];state=[]
    for r in world.targets.rows:
        state.append(None if r is None else dict(handle=[int(r.handle.kind),r.handle.identity,r.handle.generation],alive=r.alive,remaining=r.remaining,capacity=r.capacity,expires=r.expires,owner=None if r.owner is None else [int(r.owner.kind),r.owner.identity,r.owner.generation]))
    attacks=[]
    for r in data['attacks']:
        receipts=[dict(slot=slot,handle=[int(h.kind),h.identity,h.generation],delivered=receipt['delivered'],broken=receipt['broken'],took=receipt['took']) for slot,h,receipt in r['receipts']]
        attacks.append(dict(attack_id=r['attack_id'],owner=names.index(r['caster']),time=r['time'],damage=r['damage'],completed=r['completed'],receipts=receipts))
    return dict(battle=n,typed=dict(time=world.last,finished=world.finished,state=state,attacks=attacks))
def decode(block,domain,*,sampled_coefficients=None,sampled_rows=None):
    c,m,b=domain;assert block[0]==0,('battle status',block[0]);assert block[786432]==0x44425431 and not any(block[786434:786448])
    header=789248;assert block[header+2]==1 and block[header+3] in (0,1) and block[header+4]==1 and not any(block[header+5:header+16])
    assert not any(block[787456+len(c['typed_bindings'])*14:787456+128*14]),'Unbound typed state'
    state=[]
    for i in range(len(c['typed_bindings'])):
        at=787456+i*14
        if block[at+2]==0:assert not any(block[at:at+14]);state.append(None);continue
        assert block[at+3] in (0,1)
        state.append(dict(handle=list(block[at:at+3]),alive=bool(block[at+3]),remaining=number(block,at+4),capacity=number(block,at+6),expires=number(block,at+8),owner=None if block[at+10]==0xffffffff else list(block[at+10:at+13])))
        assert block[at+13]==0
    attacks=[];count=block[786433];assert count<=c['max_attacks']
    if sampled_coefficients is not None:assert len(sampled_coefficients)==count,'Native coefficient sample count'
    if sampled_rows is not None:assert len(sampled_rows)==count,'Native source sample count'
    for i in range(count):
        at=790000+i*1040;selected=block[at+3];assert 1<=selected<=128 and block[at+10] in (0,1) and not any(block[at+11:at+16])
        source=sampled_rows[i] if sampled_rows is not None else next(j for j,e in enumerate(c['effects']) if e.get('target')=='all_projectiles')
        owner=c['owners'][source]
        sampled_coefficient=(sampled_coefficients[i] if sampled_coefficients is not None else coefficient(c['effects'][source],dict(name=roster_names(c)[owner],skill_levels=skill_levels(c)[owner])))
        assert block[at+1]==m['binding_source_indices'].index(source) and struct.pack('<II',*block[at+6:at+8])==struct.pack('<d',sampled_coefficient),'Sampled typed coefficient'
        receipts=[]
        for j in range(selected):
            p=at+16+j*8;assert block[p+4] in (0,1) and block[p+5] in (0,1)
            receipts.append(dict(slot=block[p],handle=list(block[p+1:p+4]),delivered=bool(block[p+4]),broken=bool(block[p+5]),took=number(block,p+6)))
        assert not any(block[at+16+selected*8:at+1040]),'Unused typed receipts'
        attacks.append(dict(attack_id=block[at],owner=block[at+2],time=number(block,at+4),damage=number(block,at+8),completed=bool(block[at+10]),receipts=receipts))
    assert not any(block[790000+count*1040:790000+128*1040]),'Unused typed attacks'
    return dict(time=number(block,header),finished=bool(block[header+3]),state=state,attacks=attacks)
def compare(block,domain,*,coefficient_samples=None,source_samples=None):
    expected=native_reference(domain);actual=base.decoded(block,domain[1],domain[0],domain[2]);n=expected['battle']
    differences={k:(actual.get(k),v) for k,v in n.items() if k!='scope' and actual.get(k)!=v}
    assert not differences,(domain[0]['name'],differences)
    typed=decode(block,domain,sampled_coefficients=None if coefficient_samples is None else coefficient_samples(),sampled_rows=None if source_samples is None else source_samples());assert typed==expected['typed'],(domain[0]['name'],typed,expected['typed'])
    assert not any(block[L['COUNTER_CONTEXT_BASE']:L['COUNTER_CONTEXT_BASE']+1096]),'Typed counter context leaked'
    return expected
def validate_rejection(block,name):assert name.startswith('reject/destructible-battle/') and block[0]==64,(name,block[0])
