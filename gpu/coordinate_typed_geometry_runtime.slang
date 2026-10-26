// Point/shape selection reads DT liveness and WS birth times directly.
// Shapes are authored; no CPU target list, lifetime or firing schedule is stored.
static const uint TG_MAGIC=0x54474731U;
bool typedGeometryEnabled(inout Runtime s){return commands[DF_EXTRA(s)]==TG_MAGIC;}
bool validTypedGeometry(inout Runtime s)
{
    uint p=DF_EXTRA(s);
    if(commands[p]==0){for(uint i=0;i<2320;i++)if(commands[p+i]!=0)return false;return true;}
    uint n=commands[p+2],kind=commands[p+3];
    if(commands[p]!=TG_MAGIC||commands[p+1]!=1||n<1||n>128||n!=commands[p+2320]||(kind!=2&&kind!=3))return false;
    for(uint i=4;i<10;i+=2)if(!f64Finite(cNumber(p+i)))return false;
    if(f64Less(cNumber(p+8),0))return false;
    if(commands[p+11]>1)return false;
    if(commands[p+11]==1&&(commands[p+4]!=0||commands[p+5]!=0||commands[p+6]!=0||commands[p+7]!=0))return false;
    for(uint i=10;i<16;i++)if(i!=11&&commands[p+i]!=0)
    {
#ifdef PORTABLE_COORDINATE_TYPED_WEAPONS
        if(i==13&&commands[p+i]==1&&commands[p+11]==1&&f64Zero(cNumber(p+8)))continue;
#endif
#ifdef PORTABLE_COORDINATE_TYPED_AIM
        if(i==14&&commands[p+i]==1&&commands[p+13]==1)continue;
#endif
#ifdef PORTABLE_COORDINATE_TYPED_OWNERS
        if(i==12&&commands[p+i]==1&&commands[p+15]==2&&commands[p+14]==1&&commands[p+13]==1)continue;
        if(i==15&&commands[p+i]==2&&commands[p+12]==1&&commands[p+14]==1&&commands[p+13]==1)continue;
#endif
#ifdef PORTABLE_COORDINATE_TYPED_ACTORS
        if(i==15&&commands[p+i]==1&&commands[p+14]==1&&commands[p+13]==1)continue;
#endif
        return false;
    }
    for(uint slot=0;slot<128;slot++)
    {
        uint row=p+16+slot*18;
        if(slot>=n){for(uint i=0;i<18;i++)if(commands[row+i]!=0)return false;continue;}
        uint binding=p+2328+slot*12;
        if(kind==3&&(commands[binding+5]!=0||commands[binding+6]!=0||commands[binding+7]!=1))return false;
        if(commands[p+2328+slot*12+1]!=kind||commands[row+1]!=0||commands[row+16]!=0||commands[row+17]!=0)return false;
        for(uint i=2;i<16;i+=2)if(!f64Finite(cNumber(row+i)))return false;
        if(commands[row]==1){if(!f64Less(0,cNumber(row+6))||!f64Zero(cNumber(row+8))||!f64Zero(cNumber(row+10)))return false;}
        else if(commands[row]==2){if(!f64Zero(cNumber(row+6))||!f64Less(0,cNumber(row+8))||!f64Less(0,cNumber(row+10)))return false;}
        else return false;
    }
#ifdef PORTABLE_COORDINATE_TYPED_ACTORS
    if(!validTypedActorPolicy(s))return false;
#endif
    return true;
}
bool typedGeometryBefore(inout Runtime s,uint left,uint right)
{
    uint p=DF_EXTRA(s),a=p+16+left*18,b=p+16+right*18;
    uint64_t az=cNumber(a+14),bz=cNumber(b+14);
    if(!f64Equal(az,bz))return f64Less(bz,az);
    WorldSchedule w=frameSchedule(s);uint an=commands[p+2328+left*12],bn=commands[p+2328+right*12];
    uint64_t at=wsRead(wsState(w,an)+2),bt=wsRead(wsState(w,bn)+2);
    if(!f64Equal(at,bt))return f64Less(bt,at);
    return an!=bn?an>bn:left>right;
}
uint typedGeometryPick(inout Runtime s)
{
    if(!typedGeometryEnabled(s))return 0xffffffffU;
    uint p=DF_EXTRA(s),n=commands[p+2],kind=commands[p+3],best=0xffffffffU;
    uint64_t x=cNumber(p+4),y=cNumber(p+6),grow=cNumber(p+8);
    if(commands[p+11]==1){Definition d=readDefinition(s.inputBase,commands[DF_DESCRIPTOR(s)]);coordinateAimPoint(s,d.owner,x,y);}
    WorldSchedule w=frameSchedule(s);
    for(uint slot=0;slot<n;slot++)
    {
        uint state=dtAt(DF_BASE(s.resourceOutput),slot),node=commands[p+2328+slot*12],live=wsState(w,node);
        if(results[state+3]==0||results[state]!=kind)continue;
        if(kind==3&&(results[state+10]!=0||results[state+11]!=0||results[state+12]!=1))continue;
        if(results[live]==0||results[live+1]!=results[state+2]){s.error=64;return 0xffffffffU;}
        uint row=p+16+slot*18;uint64_t co=ONE,si=0;
        if(commands[row]==2)coordinateSinCosDegrees(cNumber(row+12),si,co);
        uint64_t distance=coordinateShapeDistance(commands[row],cNumber(row+2),cNumber(row+4),cNumber(row+6),cNumber(row+8),cNumber(row+10),co,si,x,y);
        if(!f64Finite(distance)){s.error=16;return 0xffffffffU;}
        if(coordinateShapeContains(distance,grow)&&(best==0xffffffffU||typedGeometryBefore(s,slot,best)))best=slot;
    }
    return best;
}
uint typedGeometryFrameSlot(inout Runtime s)
{
    uint depth=results[csMeta(s)+60];
    if(depth==0||depth>32){s.error=64;return 0xffffffffU;}
    return results[DF_SCRATCH(s.resourceOutput,depth-1)+536];
}
bool typedGeometryFrameMatch(inout Runtime s,uint at)
{
    uint slot=typedGeometryFrameSlot(s);
    return slot!=0xffffffffU&&at==dtAt(DF_BASE(s.resourceOutput),slot);
}
