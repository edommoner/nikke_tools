"""Authored hold controls and exact raw-name thresholds; no battle execution."""
import math,struct
MAGIC=0x57434831
OWNER_BASE=16
CLICK_BASE=56
SEQUENCE_BASE=696
THRESHOLD_BASE=1016
THRESHOLDS=1280
WORDS=THRESHOLD_BASE+THRESHOLDS*4

def parse_hold(timing):
 if not isinstance(timing,str) or not timing.startswith(('charge_hold:','charge_hold_count:')):return None
 parts=timing.split(':');expected=3 if parts[0]=='charge_hold_count' else 2
 if len(parts)!=expected or not parts[1]:raise ValueError('Invalid charge hold timing')
 try:seconds=float(parts[1])
 except ValueError:raise ValueError('Invalid charge hold seconds') from None
 if not math.isfinite(seconds) or seconds<0:raise ValueError('Charge hold threshold must be nonnegative finite binary64')
 count=1
 if expected==3:
  if not parts[2].isdigit() or not 1<=int(parts[2])<=2147483647:raise ValueError('Invalid charge hold event count')
  count=int(parts[2])
 return parts[1],seconds,count

def normalize_static_controls(chars,attacks,enemy,control_mode='solo'):
 from calculator.timeline import CharState
 if len(chars)!=5 or len(attacks)!=5 or len({c['name'] for c in chars})!=5:raise ValueError('Five distinct static character definitions required')
 if control_mode not in ('solo','warn','strict'):raise ValueError('Invalid control mode')
 owners=[]
 for char,attack in zip(chars,attacks):
  state=CharState(char,attack,enemy.get('code'));control=char.get('control') or {}
  reload=control.get('reload') or {}
  if (any(control.get(k) for k in ('cover','aim','burst')) or
      set(reload)-{'cancel_on_full'} or
      'cancel_on_full' in reload and type(reload['cancel_on_full']) is not bool):
   raise ValueError('Cover/reload/aim/burst controls require their own common adapters')
  clicks=[]
  for entry in state._click_sched:
   if entry.get('anchor') is not None:raise ValueError('Anchored click controls require common anchor clocks')
   gate=entry.get('gate');names=[c['name'] for c in chars]
   clicks.append(dict(mode={'auto':0,'tap':1,'hold':2,'hold_until_close':3,'hold_judge':4}[entry['mode']],window={'always':0,'burst_charge':1,'burst_chain':2,'own_full_burst':3,'after_own_fb':4}[entry['window']],priority=entry['_prio'],lead=entry.get('lead',.1),gate_stage=int(gate['burst_stage']) if gate else 0,gate_mask=(1<<names.index(gate['burst_user'])) if gate and gate['burst_user'] in names else 0))
   if entry['mode']=='tap':
    clicks[-1]['tap_timing']=dict(entry['_timing'])
  sequences=[]
  for action in state._ctrl_seq:
   if action['action']!='hold':raise ValueError('Non-hold sequence requires common physical control primitives')
   sequences.append(dict(time=float(action.get('t',0)),until=-1.0 if action.get('until') is None else float(action['until'])))
  if len(clicks)>8 or len(sequences)>8:raise ValueError('Hold control capacity exceeded')
  kind=0 if state.fire_mode!='charge' else 2 if state.input_type=='DOWN_Charge' else 1
  owners.append(dict(clicks=clicks,sequences=sequences,weapon_input=kind))
 result=dict(mode=('solo','warn','strict').index(control_mode),owners=owners)
 if any(e['mode']==1 for owner in owners for e in owner['clicks']):
  from calculator.timeline import _burst_charge_carriers
  carriers=_burst_charge_carriers(chars)
  if len(carriers)>1:raise ValueError('Only one burst-charge camera carrier is supported by the native model')
  if carriers:result['camera_override']=1<<[c['name'] for c in chars].index(carriers[0])
 return result

def compile_policy(normalized,effects,names,states,static_camera):
 if type(static_camera) is not int or not 0<=static_camera<32 or len(names)!=5 or len(set(names))!=5:raise ValueError('Invalid static camera or roster')
 mode=normalized['mode'];owners=normalized['owners']
 if 'camera_override' in normalized:
  override=normalized['camera_override']
  if type(override) is not int or not 0<override<32:raise ValueError('Invalid static native camera override')
  static_camera=override
 if type(mode) is not int or not 0<=mode<=2 or len(owners)!=5:raise ValueError('Invalid normalized control policy')
 thresholds={}
 for effect,owner in effects:
  who=names.index(owner) if isinstance(owner,str) else owner
  if type(who) is not int or not 0<=who<5:raise ValueError('Invalid charge hold owner')
  for timing in effect.get('trigger',{}).get('timing',[]):
   parsed=parse_hold(timing)
   if parsed is not None:
    raw,seconds,_=parsed;tag=states['charge_hold:'+raw]
    if type(tag) is not int or not 0<=tag<256:raise ValueError('Invalid raw hold event identity')
    thresholds[who,raw]=(tag,seconds)
 ordered=sorted(thresholds,key=lambda k:(k[0],thresholds[k][1],k[1]))
 if len(ordered)>THRESHOLDS:raise ValueError('Charge hold threshold capacity exceeded')
 tap_mask=sum(1<<who for who,owner in enumerate(owners) if any(e['mode']==1 for e in owner['clicks']))
 words=[0]*WORDS;words[:6]=[MAGIC,2 if tap_mask else 1,mode,static_camera,len(ordered),tap_mask]
 def number(value):
  if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Control literals must be finite binary64')
  return list(struct.unpack('<II',struct.pack('<d',value)))
 for who,owner in enumerate(owners):
  clicks=owner['clicks'];seq=owner['sequences'];kind=owner['weapon_input']
  if len(clicks)>8 or len(seq)>8 or type(kind) is not int or kind not in (0,1,2):raise ValueError('Invalid owner control bounds')
  keys=[k for k in ordered if k[0]==who];first=sum(k[0]<who for k in ordered);at=OWNER_BASE+who*8;words[at:at+5]=[len(clicks),len(seq),first,len(keys),kind]
  for i,e in enumerate(clicks):
   if e['mode'] not in (0,1,2,3,4) or e['window'] not in range(5) or type(e['priority']) is not int or not 0<=e['priority']<=99 or e['gate_stage'] not in range(4) or type(e['gate_mask']) is not int or not 0<=e['gate_mask']<32:raise ValueError('Invalid control row')
   if kind==0 or kind==2 and e['mode'] in (2,4):raise ValueError('Weapon input cannot hold this control')
   if (e['mode']==3)!=(e['window']==2) or (e['mode']==4)!=(e['window']==4):raise ValueError('Mismatched dynamic control window')
   if not -180<=e['lead']<=180 or e['gate_stage']==0 and e['gate_mask']!=0:raise ValueError('Invalid control lead/gate')
   at=CLICK_BASE+(who*8+i)*16;words[at:at+8]=[e['mode'],e['window'],e['priority'],e['gate_stage'],e['gate_mask'],0,*number(e['lead'])]
   if e['mode']==1:
    timing=e['tap_timing']
    if set(timing)!={'hold','charge','release','post','full_charge_interval'}:raise ValueError('Invalid literal tap timing')
    for key in ('hold','charge','release','post','full_charge_interval'):
     value=timing[key]
     if type(value) not in (int,float) or not math.isfinite(value) or not 0<=value<=180:raise ValueError('Invalid literal tap timing')
    if timing['hold']<=0:raise ValueError('Tap hold must be positive')
    for at_offset,key in zip((6,8,10,12,14),('hold','charge','release','post','full_charge_interval')):words[at+at_offset:at+at_offset+2]=number(timing[key])

  previous=-1
  for i,e in enumerate(seq):
   if kind==2 or not 0<=e['time']<=180 or e['time']<previous or not (-1==e['until'] or 0<=e['until']<=180):raise ValueError('Invalid authored hold sequence')
   at=SEQUENCE_BASE+(who*8+i)*8;words[at:at+4]=[*number(e['time']),*number(e['until'])];previous=e['time']
 for i,k in enumerate(ordered):
  tag,seconds=thresholds[k];at=THRESHOLD_BASE+i*4;words[at:at+4]=[k[0],tag,*number(seconds)]
 return words
