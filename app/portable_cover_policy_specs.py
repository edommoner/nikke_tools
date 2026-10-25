"""Literal policy descriptors; runtime anchors and reload decisions stay on GPU."""
import math,struct
INPUT_BASE=109528;INPUT_WORDS=128;OUTPUT_BASE=1769472;OUTPUT_WORDS=384
MAGIC=0x43505631;ROW_WORDS=24;STATE_WORDS=64;HISTORY=16
ANCHORS=('combat_start','fb_end','own_fb_end','next_fb_start','own_buff_end')
SOURCE='gpu/world_coordinate_policy_entry.slang'

def number(value,*,negative=False):
    if type(value) not in (int,float) or not math.isfinite(value) or not (-180 if negative else 0)<=value<=180:raise ValueError('Policy literal must be finite and bounded')
    return list(struct.unpack('<II',struct.pack('<d',value)))

def normalize(chars,attacks,enemy):
    from calculator.timeline import CharState
    if len(chars)!=5 or len(attacks)!=5:raise ValueError('Five policy owners required')
    owners=[]
    for c,atk in zip(chars,attacks,strict=True):
        control=c.get('control') or {}
        if control.get('burst'):raise ValueError('Authored burst actions need their own producer')
        state=CharState(c,atk,enemy.get('code'));when=state.reload_when
        if state.cover_policy not in ('','own_full_burst'):raise ValueError('Unknown cover policy')
        number(state.cover_extend,negative=True)
        if when is not None:
            if when['anchor'] not in ANCHORS:raise ValueError('Unknown policy anchor')
            number(when['offset'],negative=True)
        duration=state.reload_cover_dur
        if duration is not None:number(duration)
        for priority in (state.reload_priority,state.cover_priority):
            if type(priority) is not int or not 0<=priority<=99:raise ValueError('Policy priority outside private bound')
        owners.append(dict(cover=bool(state.cover_policy),extend=state.cover_extend,cover_priority=state.cover_priority,when=when,reload_priority=state.reload_priority,if_dry=state.reload_if_dry,duration=duration,cancel_on_full=state.reload_cancel_on_full))
    return owners

def pack(owners,names,tags):
    if len(owners)!=5 or len(names)!=5 or len(set(names))!=5:raise ValueError('Five distinct policy owners required')
    words=[0]*INPUT_WORDS;mask=0
    for who,o in enumerate(owners):
        if not o['cover'] and o['when'] is None and not o['cancel_on_full']:continue
        mask|=1<<who;at=8+who*ROW_WORDS;when=o['when'];gate=when.get('gate') if when else None
        buff=when.get('buff') if when else None
        if buff and buff not in tags:raise ValueError('Policy buff must bind an actual named effect')
        words[at:at+16]=[int(o['cover']),o['cover_priority'],*number(o['extend'],negative=True),ANCHORS.index(when['anchor'])+1 if when else 0,o['reload_priority'],*number(when['offset'] if when else 0,negative=True),int(bool(when and when.get('minus')=='reload_total')),int(o['if_dry']),*(number(o['duration']) if o['duration'] is not None else list(struct.unpack('<II',struct.pack('<d',-1.)))),int(gate['burst_stage']) if gate else 0,1<<names.index(gate['burst_user']) if gate and gate['burst_user'] in names else 0,tags[buff] if buff else 0xffffffff,int(o['cancel_on_full'])]
    words[:8]=[MAGIC,1,mask,5,ROW_WORDS,STATE_WORDS,HISTORY,0]
    return words

def empty():return [MAGIC,1,0,5,ROW_WORDS,STATE_WORDS,HISTORY,0]+[0]*(INPUT_WORDS-8)
