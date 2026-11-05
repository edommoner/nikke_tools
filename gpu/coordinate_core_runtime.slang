bool validCoordinateCoreIR(inout Runtime s)
{
    uint at=s.inputBase+CC_BASE_INPUT,count=commands[s.inputBase+P_WORLD_FRAME_INPUT_BASE+1];
    if(commands[at]!=CC_MAGIC||commands[at+1]!=1||commands[at+2]!=count||count==0||count>CC_NODES||commands[at+3]>1)return false;
    for(uint i=4;i<CC_HEADER;i++)if(commands[at+i]!=0)return false;
    for(uint n=0;n<CC_NODES;n++)
    {
        uint p=at+CC_HEADER+n*CC_NODE_WORDS;
        if(n<count&&commands[woNode(s,n)]==2)
        {if(!f64Finite(cNumber(p))||!f64Finite(cNumber(p+2)))return false;}
        else for(uint i=0;i<CC_NODE_WORDS;i++)if(commands[p+i]!=0)return false;
    }
    return true;
}
void coordinateCoreGeometry(inout Runtime s,inout uint64_t ax,inout uint64_t ay,out uint64_t cx,out uint64_t cy,out uint64_t diameter)
{
    diameter=cNumber(s.inputBase+P_GEOMETRY_BASE+2);cx=0;cy=0;
    uint count=commands[s.inputBase+CC_BASE_INPUT+2],selected=CC_NODES;
    uint64_t latest=0;
    // Geometry chooses greatest diameter; equal diameters prefer the newest
    // live start, then the later declared node. Base core loses an equal tie.
    for(uint n=0;n<count;n++)
    {
        if(commands[woNode(s,n)]!=2||results[woGraphState(s,n)]==0)continue;
        uint64_t value=cNumber(woNode(s,n)+8),start=actorNumber(woGraphState(s,n)+2);
        if(f64Less(value,diameter))continue;
        if(f64Equal(value,diameter)&&selected!=CC_NODES&&f64Less(start,latest))continue;
        diameter=value;selected=n;latest=start;
        uint p=s.inputBase+CC_BASE_INPUT+CC_HEADER+n*CC_NODE_WORDS;cx=cNumber(p);cy=cNumber(p+2);
    }
    if(commands[s.inputBase+CC_BASE_INPUT+3]!=0)
    {ax=f64Less(0,diameter)?cx:uint64_t(0);ay=f64Less(0,diameter)?cy:uint64_t(0);}
}
