"""Immutable boss-pattern bytecode. All transition decisions happen on the GPU."""
import math
from world_actor_specs import MAX_ACTORS,ACTOR_WORDS,packed_bindings,validate_bindings,empty_bindings
BP,BL,BW,BH,BLOG,BQ=32,8,96,512,4096,1024
ILOG=4096
NE=256
WB=16+NE
WA=WB+BP*BW
WP=WA+1+MAX_ACTORS*ACTOR_WORDS
WEAPONS=('AR','SMG','SG','SR','RL','MG')
KINDS={'idle':1,'groggy':2,'core':3,'move':4,'buff':5,'attack':6,'summon':7}
OUTCOMES={None:0,'expired':1,'followed':2,'cleared':3,'end':4}
class UnsupportedBoss(ValueError):pass

def empty_world(part_count=0):
    values=[0.0]*WP;values[WA:]=empty_bindings(part_count);return values
def validate_patterns(raw):
    from calculator.boss_pattern import validate
    from calculator.buff_manager import _TYPE_OPTIMAL_RANGE
    if not isinstance(raw,list) or len(raw)>128:raise ValueError('ボスの行動は128件以内の一覧で指定してください。')
    return validate(raw,weapon_types=frozenset(_TYPE_OPTIMAL_RANGE),squad_size=5)
def boss_effects(enemy,owner):
    """Immutable inactive definitions; GPU lifecycle activates/releases them."""
    effects=[];indices={}
    for p in validate_patterns(enemy.get('patterns',[])):
        if p.enemy_effect is not None:
            e={k:v for k,v in p.enemy_effect.items() if not k.startswith('_')}
            e.update(source='스킬1',target='target',trigger={'timing':['inactive'],'condition':[]})
            indices[p.id]=len(effects);effects.append((e,owner))
    return effects,indices

def compile_world(enemy,parts,body,program):
    from detail_world import patterns_for
    raw=body.get('enemy',{}).get('patterns',[])
    expected=patterns_for(parts)+raw
    if enemy.get('coord') is not None or enemy.get('patterns',[])!=expected:raise UnsupportedBoss('Boss world differs from validated fixed parts and authored patterns')
    all_patterns=validate_patterns(expected)
    patterns=[p for p in all_patterns if p.id!='authored-live-parts']
    if len(patterns)>BP:raise UnsupportedBoss(f'more than {BP} live boss patterns')
    names={p.id:i+1 for i,p in enumerate(patterns)};names['start']=0
    if any(p.kind not in KINDS for p in patterns):raise UnsupportedBoss('Boss kinds not yet implemented: '+', '.join(sorted({p.kind for p in patterns if p.kind not in KINDS})))
    values=empty_world();values[0]=len(patterns);values[1]=-1 if enemy.get('distance') is None else enemy['distance']
    live_indices={i:patterns.index(p) for i,p in enumerate(all_patterns) if p.id!='authored-live-parts'}
    values[WA:]=packed_bindings(all_patterns,live_indices)
    add_rows=[j for j in range(int(values[WA])) if values[WA+1+j*ACTOR_WORDS]==5]
    values[2]=sum(1<<WEAPONS.index(w) for w in set(enemy.get('optimal_range_weapons') or []))
    values[3:8]=[WEAPONS.index(c['_weapon']['weapon_type']) for c in program['chars']]
    modes=program.get('mode_weapons',[])
    values[8:8+len(modes)]=modes
    from calculator.timeline import DEFAULT_BOSS_ATK
    values[264:268]=[program.get('cover_base_hp',2000000),enemy.get('atk',DEFAULT_BOSS_ATK),add_rows[0] if add_rows else 0,1]
    if values[264]<0 or values[265]<0:raise UnsupportedBoss('Negative incoming-combat base values')
    metadata=[]
    def node(name):
        if name not in names:raise UnsupportedBoss('A live pattern references a fixed-parts lifecycle that is not implemented')
        return names[name]
    def event(name):
        special={'event:part_destroy':34,'event:projectile_destroy':35,'enemy_death':33}
        if name in special:return special[name],0
        assert name=='event:target_spawn'
        states=program['states']
        if 'target_spawn' not in states:states['target_spawn']=len(states)
        if len(states)>NE:raise UnsupportedBoss('boss events exceed named-state capacity')
        return 31,states['target_spawn']
    for i,p in enumerate(patterns):
        if max(len(p.after),len(p.until_after),len(p.emit),len(p.emit_end))>BL:raise UnsupportedBoss('more than eight boss links or emissions')
        if p.repeat>2147483647:raise UnsupportedBoss('boss repeat count exceeds int32')
        if p.until_cleared and p.summon is None:raise UnsupportedBoss('target-cleared non-summon lifecycle is not yet implemented')
        q=[0.0]*BW;q[76:80]=[p.def_mult,p.def_add,program.get('boss_effect_rows',{}).get(p.id,-1),int(p.irremovable)];q[:12]=[KINDS[p.kind],p.delay,-1 if p.until_time is None else p.until_time,p.repeat,len(p.after),len(p.until_after),p.core_px,1 if p.distance is not None else 2,p.distance or 0,sum(1<<WEAPONS.index(w) for w in set(p.weapons)),len(p.emit),len(p.emit_end)]
        if p.summon is not None:
            s=p.summon
            bound=[j for j in range(int(values[WA])) if values[WA+1+j*ACTOR_WORDS+2]==2 and values[WA+1+j*ACTOR_WORDS+3]==i]
            if len(bound)!=s.count or bound!=list(range(bound[0],bound[0]+s.count)):raise UnsupportedBoss('Summon bindings are not contiguous')
            q[89:96]=[bound[0],s.count,-1 if s.hp is None else s.hp,s.hit_hp,s.hit_hp_after,int(p.until_cleared),s.atk]
            if s.attack is not None:q[76:78]=[s.attack_at,int(s.self_destruct)]
        a=p.attack if p.attack is not None else p.summon.attack if p.summon is not None else None
        if a is not None:
            if a.debuffs:raise UnsupportedBoss('Attack-attached debuffs are not yet implemented')
            if a.hits>2147483647:raise UnsupportedBoss('Attack shot count exceeds int32')
            if p.summon is not None and a.atk is None:raise UnsupportedBoss('Summon attacks require their own attack value')
            order=sum((slot+1)<<(3*k) for k,slot in enumerate(a.slots))
            q[80:89]=[a.coeff,values[265] if a.atk is None else a.atk,{'all':1,'slot':2,'random':3,'top_atk':4}[a.rule],len(a.slots) if a.rule=='slot' else a.n,order,int(a.pierce),int(a.ignore_taunt),a.hits,a.interval]
        for k,(name,outcome) in enumerate(p.after):q[12+2*k:14+2*k]=[node(name),OUTCOMES[outcome]]
        for k,(name,delay) in enumerate(p.until_after):q[28+2*k:30+2*k]=[node(name),delay]
        for k,name in enumerate(p.emit):q[44+2*k:46+2*k]=event(name)
        for k,name in enumerate(p.emit_end):q[60+2*k:62+2*k]=event(name)
        values[WB+i*BW:WB+(i+1)*BW]=q
        metadata.append({'id':p.id,'kind':p.kind,**({'summon_name':p.summon.name} if p.summon is not None else {})})
    validate_world(values)
    return values,metadata
def validate_world(w):
    if len(w)!=WP or not all(type(v) in (int,float) and math.isfinite(v) for v in w):raise ValueError('Invalid boss bytecode size or values')
    validate_bindings(w[WA:])
    for i in range(int(w[WA])):
        row=w[WA+1+i*ACTOR_WORDS:WA+1+(i+1)*ACTOR_WORDS]
        if row[2]==2 and (row[3]>=w[0] or w[WB+int(row[3])*BW]!=7):raise ValueError('Summon actor has no compatible lifecycle')
    def integer(v,lo,hi):return int(v)==v and lo<=v<=hi
    if not integer(w[0],0,BP) or w[1]<-1 or not integer(w[2],0,63):raise ValueError('Invalid boss world header')
    if any(not integer(v,0,5) for v in w[3:8]) or any(not integer(v,-1,5) for v in w[8:264]):raise ValueError('Invalid boss weapon metadata')
    add_rows=[i for i in range(int(w[WA])) if w[WA+1+i*ACTOR_WORDS]==5]
    if w[264]<0 or w[265]<0 or w[266]!=(add_rows[0] if add_rows else 0) or w[267] not in (0,1) or any(w[268:WB]):raise ValueError('Invalid incoming world header')
    for i in range(int(w[0])):
        q=w[WB+i*BW:WB+(i+1)*BW]
        if not integer(q[0],1,7) or q[1]<0 or q[2]!=-1 and q[2]<=0 or not integer(q[3],0,2147483647):raise ValueError('Invalid boss lifecycle')
        if not integer(q[4],1,BL) or any(not integer(q[k],0,BL) for k in (5,10,11)):raise ValueError('Invalid boss link count')
        if not integer(q[6],0,2147483647) or not integer(q[7],1,2) or q[8]<0 or not integer(q[9],0,63):raise ValueError('Invalid live boss overlay')
        if q[76]<0 or not integer(q[78],-1,NE-1) or not integer(q[79],0,1):raise ValueError('Invalid boss buff overlay')
        if q[0]==6 or q[0]==7 and q[80]>0:
            if q[80]<=0 or q[81]<0 or not integer(q[82],1,4) or not integer(q[83],0,5) or not integer(q[84],0,32767) or any(q[k] not in (0,1) for k in (85,86)) or not integer(q[87],1,2147483647) or q[88]<0:raise ValueError('Invalid incoming attack')
            if q[82]==2:
                order=int(q[84]);slots=[]
                while order:slots.append((order&7)-1);order>>=3
                if len(slots)!=q[83] or len(set(slots))!=len(slots) or any(s<0 or s>=5 for s in slots):raise ValueError('Invalid incoming attack slots')
            elif q[84]!=0 or q[82] in (3,4) and q[83]<1:raise ValueError('Invalid incoming target count')
        elif any(q[80:89]):raise ValueError('Attack fields on non-attack pattern')
        if q[0]==7:
            first,count,hp,hit_hp,delay,cleared,atk=q[89:96]
            if not integer(first,1,MAX_ACTORS-1) or not integer(count,1,MAX_ACTORS-1) or first+count>w[WA] or hp!=-1 and hp<=0 or not integer(hit_hp,0,2147483647) or hp==-1 and not hit_hp or delay<0 or cleared not in (0,1) or atk<0:raise ValueError('Invalid summon source')
            if (hp>0 and hit_hp>0 and delay<=0) or (not (hp>0 and hit_hp>0) and delay!=0):raise ValueError('Invalid summon hit-HP transition')
            if q[77] not in (0,1) or not q[80] and (q[76]!=1 or q[77]!=0):raise ValueError('Invalid summon attack controls')
            for slot in range(int(count)):
                row=w[WA+1+(int(first)+slot)*ACTOR_WORDS:WA+1+(int(first)+slot+1)*ACTOR_WORDS]
                if row[0]!=5 or row[2]!=2 or row[3]!=i or row[4]!=slot:raise ValueError('Summon binding differs from source pool')
        elif any(q[89:]):raise ValueError('Unknown incoming attack fields')
        for k in range(int(q[4])):
            if not integer(q[12+2*k],0,w[0]) or not integer(q[13+2*k],0,3):raise ValueError('Invalid boss dependency')
        for k in range(int(q[5])):
            if not integer(q[28+2*k],1,w[0]) or q[29+2*k]<0:raise ValueError('Invalid boss until dependency')
        for base,count in ((44,int(q[10])),(60,int(q[11]))):
            for k in range(count):
                code,tag=q[base+2*k:base+2*k+2]
                if code not in (31,33,34,35) or not integer(tag,0,NE-1):raise ValueError('Invalid boss emission')
