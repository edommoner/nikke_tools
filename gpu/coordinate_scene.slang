// Read-only coordinate descriptors; liveness comes from the caller's pool view.
#include "coordinate_scene_layout.slang"
struct CoordinateScene {uint input,output,count,state,error;};
uint64_t cNumber(uint at) {return uint64_t(commands[at])|(uint64_t(commands[at+1])<<32);}
void cStore(uint at,uint64_t v) {results[at]=uint(v);results[at+1]=uint(v>>32);}
uint cRow(CoordinateScene s,uint row) {return s.input+C_ROW_BASE+row*C_ROW_WORDS;}
uint cState(CoordinateScene s,uint row) {return s.state+row*8;}
bool cValidate(CoordinateScene s,uint patterns)
{
    if(s.count>C_CAPACITY||patterns==0||patterns>32)return false;
    for(uint i=0;i<C_ROWS;i++)
    {
        uint at=cRow(s,i);
        if(i>=s.count){for(uint k=0;k<C_ROW_WORDS;k++)if(commands[at+k]!=0)return false;continue;}
        if((commands[at]!=1&&commands[at]!=6)||commands[at+1]>=C_CAPACITY||commands[at+2]>=patterns||commands[at+3]>=C_CAPACITY||commands[at+5]==0||commands[at+5]>=C_ROWS)return false;
        for(uint j=6;j<22;j+=2)if(!f64Finite(cNumber(at+j)))return false;
        if(f64Less(cNumber(at+20),0)||commands[at+22]!=0||commands[at+23]!=0)return false;
        if(commands[at+4]==1){if(!f64Less(0,cNumber(at+10))||!f64Zero(cNumber(at+12))||!f64Zero(cNumber(at+14))||!f64Zero(cNumber(at+16)))return false;}
        else if(commands[at+4]==2){if(!f64Zero(cNumber(at+10))||!f64Less(0,cNumber(at+12))||!f64Less(0,cNumber(at+14)))return false;}
        else return false;
        for(uint j=0;j<i;j++)
        {
            uint b=cRow(s,j);
            if(commands[at+5]==commands[b+5]||(commands[at]==commands[b]&&commands[at+1]==commands[b+1])||(commands[at+2]==commands[b+2]&&commands[at+3]==commands[b+3]))return false;
        }
    }
    return true;
}
bool cBefore(CoordinateScene s,uint a,uint b)
{
    uint x=cRow(s,a),y=cRow(s,b);uint64_t az=cNumber(x+18),bz=cNumber(y+18);
    if(f64Less(az,bz))return false;if(f64Less(bz,az))return true;
    uint ax=cState(s,a),by=cState(s,b);uint64_t at=uint64_t(results[ax+4])|(uint64_t(results[ax+5])<<32),bt=uint64_t(results[by+4])|(uint64_t(results[by+5])<<32);
    if(f64Less(at,bt))return false;if(f64Less(bt,at))return true;
    if(commands[x+2]!=commands[y+2])return commands[x+2]>commands[y+2];return commands[x+3]>commands[y+3];
}
void cCapture(CoordinateScene s,uint destination,uint64_t time)
{
    uint order[128];uint count=0;
    for(uint i=0;i<s.count;i++)if(results[cState(s,i)+1]!=0)
    {
        uint at=count;while(at>0&&cBefore(s,i,order[at-1])){order[at]=order[at-1];at--;}
        order[at]=i;count++;
    }
    cStore(destination,time);results[destination+2]=count;uint parts=0;
    for(uint i=0;i<count;i++)
    {
        uint row=order[i],r=cRow(s,row),state=cState(s,row),dst=destination+8+i*4;
        results[dst]=commands[r+5];results[dst+1]=commands[r];results[dst+2]=commands[r+1];results[dst+3]=results[state];
        if(commands[r]==1)
        {
            uint to=destination+8+C_ROWS*4+parts*4;for(uint j=0;j<4;j++)results[to+j]=results[dst+j];parts++;
        }
    }
    results[destination+3]=parts;
}
