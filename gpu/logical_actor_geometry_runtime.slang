// Opt-in normal-shot descriptors; all presence/health remains in ActorPool.
#include "logical_actor_geometry_layout.slang"
uint lagInput(inout Runtime s){return s.inputBase+LAG_BASE;}
uint lagShape(inout Runtime s,uint slot)
{
    uint index=commands[lagInput(s)+LAG_MAP_BASE+slot];
    return index==0?0:lagInput(s)+LAG_ROW_BASE+(index-1)*LAG_ROW_WORDS;
}
uint lagHead(inout Runtime s){return s.resourceOutput+LAG_HEAD_BASE;}
uint lagPellet(inout Runtime s,uint hit){return s.resourceOutput+LAG_PELLET_BASE+hit*2;}
bool lagActive(inout Runtime s){return results[lagHead(s)]!=0;}
bool validLogicalActorGeometry(inout Runtime s)
{
    uint p=lagInput(s),count=commands[p+2];
    if(commands[p]!=LAG_MAGIC||commands[p+1]!=LAG_VERSION||count==0||count>LAG_ROWS||commands[p+3]!=actorPoolCount(s))return false;
    for(uint i=4;i<LAG_HEADER;i++)if(commands[p+i]!=0)return false;
    for(uint index=0;index<LAG_ROWS;index++)
    {
        uint row=p+LAG_ROW_BASE+index*LAG_ROW_WORDS;
        if(index>=count){for(uint j=0;j<LAG_ROW_WORDS;j++)if(commands[row+j]!=0)return false;continue;}
        uint slot=commands[row],kind=commands[row+6];
        if(slot==0||slot>=actorPoolCount(s)||commands[p+LAG_MAP_BASE+slot]!=index+1)return false;
        uint b=actorBinding(s,slot);
        if(commands[row+1]!=5||commands[b]!=5||commands[b+2]!=2||commands[b+3]>=32)return false;
        for(uint j=1;j<6;j++)if(commands[row+j]!=commands[b+j-1])return false;
        if(commands[row+7]!=0||kind!=1&&kind!=2)return false;
        for(uint j=8;j<26;j+=2)if(!f64Finite(cNumber(row+j)))return false;
        uint64_t radius=cNumber(row+12),width=cNumber(row+14),height=cNumber(row+16);
        if(kind==1?(!f64Less(0,radius)||!f64Zero(width)||!f64Zero(height)):(!f64Zero(radius)||!f64Less(0,width)||!f64Less(0,height)))return false;
        uint64_t co=ONE,si=0;if(kind==2)coordinateSinCosDegrees(cNumber(row+18),si,co);
        if(cNumber(row+22)!=co||cNumber(row+24)!=si)return false;
        for(uint j=26;j<LAG_ROW_WORDS;j++)if(commands[row+j]!=0)return false;
    }
    for(uint slot=0;slot<LAG_MAP_WORDS;slot++)
    {
        uint index=commands[p+LAG_MAP_BASE+slot];if(index==0)continue;
        if(slot==0||slot>=actorPoolCount(s)||index>count||commands[p+LAG_ROW_BASE+(index-1)*LAG_ROW_WORDS]!=slot)return false;
    }
    for(uint i=LAG_MAP_BASE+LAG_MAP_WORDS;i<LAG_WORDS;i++)if(commands[p+i]!=0)return false;
    return true;
}
bool lagBefore(inout Runtime s,uint a,uint b)
{
    uint ar=lagShape(s,a),br=lagShape(s,b);
    uint64_t az=ar!=0?cNumber(ar+20):cNumber(cRow(coordinatePoolView(s),commands[coordinateAreaRow(s,a)]-1)+18);
    uint64_t bz=br!=0?cNumber(br+20):cNumber(cRow(coordinatePoolView(s),commands[coordinateAreaRow(s,b)]-1)+18);
    if(!f64Equal(az,bz))return f64Less(bz,az);
    uint64_t at=actorNumber(actorPoolAt(s,a)+8),bt=actorNumber(actorPoolAt(s,b)+8);
    if(!f64Equal(at,bt))return f64Less(bt,at);
    uint ab=actorBinding(s,a),bb=actorBinding(s,b);
    if(commands[ab+3]!=commands[bb+3])return commands[ab+3]>commands[bb+3];
    if(commands[ab+4]!=commands[bb+4])return commands[ab+4]>commands[bb+4];
    return ar!=0&&br==0;
}
void lagSnapshot(inout Runtime s,uint who)
{
    uint h=csMeta(s),head=lagHead(s);results[head]=uint(WORLD_PACKET_NORMAL(s,who));
    if(!lagActive(s))return;
    results[head+1]=results[actorPoolAt(s,0)];
    uint n=results[h+3],p=lagInput(s),count=commands[p+2];
    for(uint index=0;index<count;index++)
    {
        uint row=p+LAG_ROW_BASE+index*LAG_ROW_WORDS,slot=commands[row],state=actorPoolAt(s,slot);
        if(results[state+1]==0)continue;
        if(n>=127U||results[state]==0){s.error=64;return;}
        uint j=n;
        while(j>0&&lagBefore(s,slot,results[h+CS_FRAME+(j-1)*4]))
        {
            for(uint k=0;k<4;k++)results[h+CS_FRAME+j*4+k]=results[h+CS_FRAME+(j-1)*4+k];
            j--;
        }
        uint e=h+CS_FRAME+j*4;
        results[e]=slot;results[e+1]=5;results[e+2]=commands[row+2];results[e+3]=results[state];n++;
    }
    results[h+3]=n;
}
bool lagContains(inout Runtime s,uint row,uint64_t x,uint64_t y,uint64_t grow)
{
#ifdef PORTABLE_ENEMY_MOVEMENT
    uint64_t d=coordinateShapeDistance(commands[row+6],enemyMovementPosition(s,row,0),enemyMovementPosition(s,row,1),cNumber(row+12),cNumber(row+14),cNumber(row+16),cNumber(row+22),cNumber(row+24),x,y);
#else
    uint64_t d=coordinateShapeDistance(commands[row+6],cNumber(row+8),cNumber(row+10),cNumber(row+12),cNumber(row+14),cNumber(row+16),cNumber(row+22),cNumber(row+24),x,y);
#endif
    if(!f64Finite(d)){s.error=16;return false;}return coordinateShapeContains(d,grow);
}
uint64_t lagAmount(inout Runtime s,uint hit,uint kind)
{
    return actorNumber(lagActive(s)&&kind==5?lagPellet(s,hit):csRow(s,hit)+(kind==1?4:6));
}
