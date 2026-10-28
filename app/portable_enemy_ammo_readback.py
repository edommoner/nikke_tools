"""Decode only owned enemy-ammunition state; full battle remains existing code."""
import struct
from portable_enemy_ammo_wire import LAYOUT as E
from portable_specs import LIMITS as L


def compare_ammo(block,domain,native,*,allow_retired_queue=False):
    case,meta,bindings,_=domain;data=native['enemy_ammo'];head=E['OUTPUT_BASE']
    number=lambda at:struct.unpack('<d',struct.pack('<II',*block[at:at+2]))[0]
    actor=lambda slot,gen:[int(bindings[slot].kind),bindings[slot].identity,gen]
    label=lambda slot:bindings[slot].label
    names={v:k for k,v in meta['states'].items()}
    histories=block[head+1];events=block[head+2]
    assert block[head]==0x45414d31 and histories<=E['HISTORIES'] and events<=E['EVENTS']
    assert not any(block[head+3:head+16])
    generations=[];final=[];last={}
    for i in range(histories):
        at=head+E['HISTORY_BASE']+i*12;slot,gen,cap,initial,remaining,alive=block[at:at+6]
        assert slot<len(bindings) and gen>0 and 0<=remaining<=cap and alive in (0,1) and not any(block[at+10:at+12])
        generations.append(dict(time=number(at+8),label=label(slot),actor=actor(slot,gen),initial=initial,capacity=cap))
        final.append(dict(label=label(slot),actor=actor(slot,gen),alive=bool(alive),capacity=cap,remaining=remaining,reloading_until=number(at+6)))
        last[slot]=(i,at)
    assert generations==data['generations'] and final==data['final'],'Every original and superseded magazine generation'
    for slot in range(128):
        at=head+E['STATE_BASE']+slot*8
        if slot not in last:assert not any(block[at:at+8]);continue
        index,h=last[slot]
        assert list(block[at:at+5])==[block[h+1],block[h+4],block[h+6],block[h+7],index+1]
        assert not any(block[at+5:at+8])
    assert not any(block[head+E['HISTORY_BASE']+histories*12:head+E['EVENT_BASE']])
    charges=[];reloads=[];attempts=[];current=None
    for i in range(events):
        at=head+E['EVENT_BASE']+i*16;kind=block[at]
        if kind==1:
            row,owner,name=block[at+1:at+4]
            mapping=meta.get('binding_source_indices');source=mapping[row] if mapping is not None else row
            from portable_enemy_ammo_wire import enemy_percentage
            assert source<len(case['effects']) and enemy_percentage(case['effects'][source])
            current=dict(time=number(at+4),name=names[name],caster=case['names'][owner],value=number(at+6),targets=[],completion=[])
            charges.append(current);current_count=block[at+8];current_row=row
            assert not any(block[at+9:at+16])
        elif kind==2:
            assert current is not None and block[at+1]==current_row and number(at+8)==current['time']
            slot,gen,cap,before,after=block[at+2:at+7]
            current['targets'].append(dict(label=label(slot),actor=actor(slot,gen),capacity=cap,before=before,after=after,change=after-before))
            assert block[at+7]==0 and not any(block[at+10:at+16])
        elif kind==3:
            assert current is not None and block[at+1]==current_row and names[block[at+2]]==current['name'] and case['names'][block[at+3]]==current['caster']
            assert number(at+4)==current['time'] and block[at+6]==current_count==len(current['targets'])
            current['completion'].append(dict(event='event:'+current['name'],time=current['time'],remaining={r['label']:r['after'] for r in current['targets']}))
            assert not any(block[at+7:at+16])
        elif kind in (4,5,6):
            slot,gen,before,after=block[at+1:at+5]
            row=dict(kind={4:'start',5:'complete',6:'cancel'}[kind],time=number(at+6),label=label(slot),actor=actor(slot,gen),before=before,after=after)
            if kind!=6:row['deadline']=number(at+8)
            reloads.append(row)
            assert block[at+5]==0 and not any(block[at+10:at+16])
        elif kind==7:
            record,slot,gen,before,after,status,index=block[at+1:at+8];node=block[at+10]
            row=dict(time=number(at+8),label=label(slot),actor=actor(slot,gen),pattern=case['patterns'][node]['id'],index=index,status={1:'fired',2:'reloading',3:'empty',4:'dead',5:'stale'}[status])
            if status<=3:row.update(before=before,after=after)
            else:assert before==after==0
            original=L['WORLD_FRAME_OUTPUT_BASE']+2832+record*6
            assert block[original]==3 and block[original+1]==node and block[original+2]==index
            assert (block[original+5]!=0)==(status==1),'Blocked attempts cannot select targets, draw RNG or issue damage'
            if allow_retired_queue:
                assert block[at+11] in (0,1)
                if block[at+11]:
                    assert status<=3 and slot>0
                    row['retired_queue']=True
            else:assert block[at+11]==0
            attempts.append(row);assert not any(block[at+12:at+16])
        else:raise AssertionError('Unknown enemy ammo receipt kind')
    assert charges==data['charges'],'Original percentage quantities, recipient order and completion snapshots'
    assert reloads==data['reloads'] and attempts==data['attempts'],'Real resource gates and native frame deadlines'
    assert not any(block[head+E['EVENT_BASE']+events*16:head+E['EVENT_BASE']+E['EVENTS']*16])
    clean=list(block);end=head+E['EVENT_BASE']+E['EVENTS']*16;clean[head:end]=[0]*(end-head)
    return compare_resources(clean,domain,native)


def compare_resources(block,domain,native):
    """Audit every shared resource receipt before projecting its legacy prefix."""
    from portable_resource_decode import resource_readback
    case,meta,*_=domain;observed=native['original_resources'];h=L['RESOURCE_HEADER_BASE']
    count,total=block[h:h+2];assert count==total==len(observed['ordered_notifications']) and count<=E['RESOURCE_CAPACITY']
    assert not any(block[h+2:h+8])
    number=lambda words,at:struct.unpack('<d',struct.pack('<II',*words[at:at+2]))[0]
    continuation=E['OUTPUT_BASE']+E['RESOURCE_BASE'];trace=[]
    for i in range(count):
        at=L['RESOURCE_TRACE_BASE']+i*8 if i<128 else continuation+(i-128)*8
        event,owner,key,reserved=block[at:at+4]
        assert event in (26,30) and owner<5 and key<len(meta['resource_names']) and reserved==0
        trace.append(dict(event=event,owner=owner,resource=meta['resource_names'][key],time=number(block,at+4),boundary=number(block,at+6)))
    assert trace==observed['ordered_notifications'],'Every gauge boundary and ammo consumption notice in native order'
    end=continuation+(E['RESOURCE_CAPACITY']-128)*8
    assert not any(block[continuation+max(0,count-128)*8:end]),'Unused resource history continuation'
    clean=list(block);clean[h]=min(count,128);clean[continuation:end]=[0]*(end-continuation)
    decoded=resource_readback(clean,meta,L,lambda at:number(clean,at))
    for who,owner in enumerate(case['names']):
        state=observed['final'].get(owner,{})
        assert {key for key in state if not key.startswith('_gauge_max:')}<=set(meta['resource_names'])
        for key in meta['resource_names']:
            cap='_gauge_max:'+key
            assert decoded['resources'][who][key]==dict(present=key in state,value=state.get(key,0),cap_present=cap in state,base_cap=state.get(cap)),'Every final shared resource quantity and cap'
    for index,source in enumerate(meta['binding_source_indices']):
        if case['effects'][source].get('stat') in ('gauge_charge','gauge_consume','gauge_consume_as_ammo'):
            assert block[L['STATE_BASE']+index*10+8]==sum(r['row']==source for r in observed['dispatches']),'Every original resource dispatch activation'
    return clean
