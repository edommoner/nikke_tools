"""Authored boss patterns and fixed parts shared by CPU and GPU preparation."""
import copy,math
MAX_PARTS=32
EN=68

def read_parts(value):
    if not isinstance(value,list) or len(value)>MAX_PARTS:raise ValueError('パーツは32個以内の一覧で指定してください。')
    parts=[];names=set()
    for item in value:
        if not isinstance(item,dict) or set(item)!={'name','hp','reach'}:raise ValueError('パーツには name・hp・reach を指定してください。')
        name=item['name'];hp=item['hp'];reach=item['reach']
        if not isinstance(name,str) or not name.strip() or len(name)>80 or name in names:raise ValueError('パーツ名は重複しない80文字以内の名前にしてください。')
        if isinstance(hp,bool) or not isinstance(hp,(int,float)) or not math.isfinite(hp) or not 0<=hp<=1e15:raise ValueError('パーツHPは0〜1,000,000,000,000,000で指定してください。0は破壊されない対象です。')
        if type(reach) is not int or not 1<=reach<=5:raise ValueError('パーツの到達段階は1〜5の整数です。')
        names.add(name);parts.append(dict(name=name,hp=hp,reach=reach))
    return parts

def patterns_for(parts):
    if not parts:return []
    return [dict(id='authored-live-parts',kind='parts',targets=[{**p,'emit_on_destroy':['event:part_destroy']} for p in parts])]

def prepare_enemy(enemy):
    enemy=copy.deepcopy(enemy)
    parts=read_parts(enemy.pop('parts',[]))
    raw=enemy.pop('patterns',[])
    if not isinstance(raw,list) or len(raw)>128:raise ValueError('ボスの行動は128件以内の一覧で指定してください。')
    if raw or parts:enemy['patterns']=patterns_for(parts)+raw
    return enemy

def packed_enemy(enemy,parts):
    if not parts and not enemy.get('has_parts',False):return [enemy['def'],enemy['core_px']]
    row=[0.0]*EN;row[:3]=[enemy['def'],enemy['core_px'],len(parts)];row[67]=int(bool(enemy.get('has_parts',False)))
    for i,p in enumerate(parts):row[3+i*2:5+i*2]=[p['hp'],p['reach']]
    return row

def cpu_parts_state(parts,result):
    out=[]
    for part in parts:
        hits=[hit for hit in result.hits if hit.part==part['name']]
        destroyed=next((event for event in result.boss_log if event.event=='destroy' and event.detail==part['name']),None)
        out.append(dict(name=part['name'],damage=sum(hit.damage for hit in hits),hits=len(hits),destroyed=destroyed is not None,
                        destroyed_at=round(destroyed.t,6) if destroyed is not None else None))
    return out
