StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
#include "binary64.slang"
#include "coordinate_scene.slang"
// Lifecycle driver only. The shared selector reads a caller-owned live pool.
[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id:SV_DispatchThreadID)
{
    if(id.x>=commands[0])return;
    uint input=1+id.x*C_INPUT,output=id.x*C_OUTPUT;
    for(uint i=0;i<C_OUTPUT;i++)results[output+i]=0;
    CoordinateScene s;s.input=input;s.output=output;s.count=commands[input+2];s.state=output+C_STATE;s.error=0;
    uint patterns=commands[input+3],ops=commands[input+4];
    if(commands[input]!=0x434f4f31U||commands[input+1]!=1||ops==0||ops>C_OPS||!cValidate(s,patterns)){results[output]=64;return;}
    for(uint i=5;i<16;i++)if(commands[input+i]!=0){results[output]=64;return;}
    uint64_t previous=0;
    for(uint i=0;i<C_OPS;i++)
    {
        uint at=input+C_OP_BASE+i*C_OP_WORDS;
        if(i>=ops){for(uint j=0;j<C_OP_WORDS;j++)if(commands[at+j]!=0){results[output]=64;return;}continue;}
        uint op=commands[at],index=commands[at+1];uint64_t time=cNumber(at+2),amount=cNumber(at+4);
        if(op<1||op>4||!f64Finite(time)||f64Less(time,0)||f64Less(time,previous)||!f64Finite(amount)||f64Less(amount,0)||commands[at+6]!=0||commands[at+7]!=0||((op==1||op==2)&&(index>=patterns||!f64Zero(amount)))||op==3&&index>=s.count||op==4&&(index!=0||!f64Zero(amount))){results[output]=64;return;}
        previous=time;
    }
    for(uint i=0;i<C_ROWS*C_ROW_WORDS;i++)results[output+C_DESC+i]=commands[input+C_ROW_BASE+i];
    uint generations[32];uint active[32];for(uint i=0;i<32;i++){generations[i]=0;active[i]=0;}
    uint queries=0;
    for(uint i=0;i<ops;i++)
    {
        uint at=input+C_OP_BASE+i*C_OP_WORDS,op=commands[at],index=commands[at+1];uint64_t time=cNumber(at+2);
        if(op==1)
        {
            if(active[index]!=0||generations[index]==0x7fffffffU){results[output]=64;return;}
            active[index]=1;generations[index]++;
            for(uint j=0;j<s.count;j++)if(commands[cRow(s,j)+2]==index)
            {uint st=cState(s,j);for(uint k=0;k<8;k++)results[st+k]=0;results[st]=generations[index];results[st+1]=1;cStore(st+4,time);}
        }
        else if(op==2)
        {
            if(active[index]==0){results[output]=64;return;}active[index]=0;
            for(uint j=0;j<s.count;j++)if(commands[cRow(s,j)+2]==index)results[cState(s,j)+1]=0;
        }
        else if(op==3)
        {
            uint st=cState(s,index),row=cRow(s,index);
            if(results[st+1]!=0)
            {
                uint64_t damage=f64Add(uint64_t(results[st+2])|(uint64_t(results[st+3])<<32),cNumber(at+4));cStore(st+2,damage);results[st+6]++;
                uint64_t hp=cNumber(row+20);if(!f64Zero(hp)&&!f64Less(damage,hp))results[st+1]=0;
            }
        }
        else {cCapture(s,output+C_QUERIES+queries*C_SNAPSHOT,time);queries++;}
    }
    results[output+1]=queries;results[output+2]=s.count;results[output+3]=0x434f4f31U;
}
