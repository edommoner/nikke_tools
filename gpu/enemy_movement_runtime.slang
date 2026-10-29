// Shared existing-carrier/actor/frame consumer. No independent effect timer.
#include "enemy_movement_math.slang"
uint emInput(inout Runtime s){return s.inputBase+EMB_BASE;}
uint emOutput(inout Runtime s){return s.resourceOutput+EMB_OUT;}
uint emState(inout Runtime s,uint slot){return emOutput(s)+EMB_STATE+slot*EMB_STATE_WORDS;}
uint emKind(inout Runtime s,Definition d)
{
    if(d._wireRow>=s.count)return 0;
    uint p=emInput(s);if(commands[p]!=EMB_MAGIC||commands[p+1]!=1)return 0;
    return commands[p+EMB_MAP+d._wireRow];
}
bool enemyMovementMarker(inout Runtime s,Definition d)
{
    uint k=emKind(s,d);
    return k>=1&&k<=2&&d.kind==0&&d.stat==0&&d.enemyBuff==1&&d.damageRoute==2&&d.maxStack==1
        &&f64Zero(d.value)&&f64Equal(d.duration,f64FromI64(k==1?5:2));
}
bool initializeEnemyMovement(inout Runtime s)
{
    uint p=emInput(s),n=commands[p+2];
    if(commands[p]!=EMB_MAGIC||commands[p+1]!=1||n<1||n>127||n!=commands[lagInput(s)+2]||commands[p+3]!=s.count||commands[p+4]!=actorPoolCount(s)||commands[p+5]>1)return false;
    for(uint i=6;i<EMB_HEADER;i++)if(commands[p+i]!=0)return false;
    uint marked=0;
    for(uint row=0;row<256;row++)
    {
        uint kind=commands[p+EMB_MAP+row];if(kind==0)continue;
        if(row>=s.count||kind>2||!enemyMovementMarker(s,readDefinition(s.inputBase,row)))return false;
        marked++;
    }
    if(marked==0)return false;
    for(uint i=0;i<127;i++)
    {
        uint r=p+EMB_ROWS+i*EMB_ROW_WORDS;
        if(i>=n){for(uint j=0;j<EMB_ROW_WORDS;j++)if(commands[r+j]!=0)return false;continue;}
        uint slot=commands[r],shape=lagInput(s)+LAG_ROW_BASE+i*LAG_ROW_WORDS;
        if(slot==0||slot>=actorPoolCount(s)||commands[shape]!=slot||commands[actorBinding(s,slot)]!=5)return false;
        for(uint j=1;j<4;j++)if(commands[r+j]!=0)return false;
        for(uint j=4;j<12;j+=2)if(!f64Finite(loadNumber(r+j)))return false;
    }
    results[emOutput(s)]=EMB_MAGIC;return true;
}
bool emField(inout Runtime s,uint carrier,uint slot)
{
    Definition d=residentDefinition(s,carrier);uint kind=emKind(s,d);
    return kind>=1&&kind<=2&&s.alive[carrier]!=0&&actorFieldMember(s,carrier,ACTOR_REF|slot);
}
uint emFlags(inout Runtime s,uint slot,uint64_t when)
{
    uint flags=0;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];if(!emField(s,row,slot)||f64Less(when,s.activated[row])||!f64Less(when,s.end[row])||!actorFieldConditions(s,row,ACTOR_REF|slot,when))continue;
        flags|=emKind(s,residentDefinition(s,row))==1?1:2;
    }
    return flags;
}
uint64_t emBoundary(inout Runtime s,uint slot,uint64_t left,uint64_t end)
{
    uint64_t right=end;
    for(uint pass=0;pass<s.orderedCount;pass++)
    {
        uint row=s.orderedRows[pass];if(!emField(s,row,slot))continue;
        if(f64Less(left,s.activated[row])&&f64Less(s.activated[row],right))right=s.activated[row];
        if(f64Less(left,s.end[row])&&f64Less(s.end[row],right))right=s.end[row];
    }
    return right;
}
void enemyMovementFrame(inout Runtime s,uint64_t when)
{
    uint p=emInput(s),head=emOutput(s);
    if(results[head]!=EMB_MAGIC){s.error=64;return;}
    for(uint i=0;i<commands[p+2]&&s.error==0;i++)
    {
        uint input=p+EMB_ROWS+i*EMB_ROW_WORDS,slot=commands[input],actor=actorPoolAt(s,slot),gen=results[actor],st=emState(s,slot);
        if(gen==0)continue;
        if(results[st+8]!=0&&results[st]==gen&&f64Equal(actorNumber(st+2),when))continue;
        if(results[st+8]==0||results[st]!=gen)
        {
            uint shape=lagShape(s,slot);results[st]=gen;results[st+8]=1;
            storeNumber(st+2,when);storeNumber(st+4,loadNumber(shape+8));storeNumber(st+6,loadNumber(shape+10));
        }
        uint64_t left=actorNumber(st+2),x=actorNumber(st+4),y=actorNumber(st+6);
        if(f64Less(when,left)){s.error=64;return;}
        uint first=results[head+2];
        if(results[actor+1]!=0)
        {
            uint iterations=0;
            while(f64Less(left,when)&&s.error==0)
            {
                if(iterations++>1024){s.error=2;return;}
                uint64_t right=emBoundary(s,slot,left,when),ox,oy;
                if(!f64Less(left,right)){s.error=64;return;}
                uint flags=emFlags(s,slot,left);
                if(!enemyMovementStep(x,y,loadNumber(input+4),loadNumber(input+6),loadNumber(input+8),loadNumber(input+10),f64Add(right,left^F64_SIGN),(flags&1)!=0,(flags&2)!=0,commands[p+5],ox,oy)){s.error=16;return;}
                uint count=results[head+2];if(count>=EMB_CAPACITY){s.error=2;return;}
                uint record=head+EMB_SEGMENTS+count*EMB_SEGMENT_WORDS;results[head+2]=count+1;
                results[record]=slot;results[record+1]=gen;results[record+2]=flags;
                storeNumber(record+4,left);storeNumber(record+6,right);storeNumber(record+8,x);storeNumber(record+10,y);storeNumber(record+12,ox);storeNumber(record+14,oy);
                left=right;x=ox;y=oy;
            }
        }
        results[st+1]=results[actor+1];storeNumber(st+2,when);storeNumber(st+4,x);storeNumber(st+6,y);
        uint count=results[head+1];if(count>=EMB_CAPACITY){s.error=2;return;}
        uint record=head+EMB_FRAMES+count*EMB_FRAME_WORDS;results[head+1]=count+1;
        results[record]=slot;results[record+1]=gen;results[record+2]=results[actor+1];results[record+3]=first;results[record+4]=results[head+2]-first;
        storeNumber(record+6,when);storeNumber(record+8,x);storeNumber(record+10,y);
    }
}
uint64_t enemyMovementPosition(inout Runtime s,uint shape,uint axis)
{
    uint slot=commands[shape],st=emState(s,slot);
    if(results[emOutput(s)]!=EMB_MAGIC||results[st+8]==0||results[st]!=results[actorPoolAt(s,slot)]){s.error=64;return 0;}
    return actorNumber(st+4+axis*2);
}
