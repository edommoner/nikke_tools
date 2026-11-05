// combat-prefilter-metal-f32-v1: literal port of app/combat.cu's approximate model.
// Float32 inputs, arithmetic, clock and accumulators; never a final score.
#define CS 44
#define ES 12
#define NS 24
#define ME 160
float hi(float a,float b){return a>b?a:b;}
float lo(float a,float b){return a<b?a:b;}
// Metal round() uses ties away from zero. Preserve CUDA RN ties-to-even.
float roundDamage(float x){
 float lower=floor(x),fraction=x-lower;
 return fraction<0.5f?lower:fraction>0.5f?lower+1.0f:fmod(lower,2.0f)==0.0f?lower:lower+1.0f;
}
// Each invocation owns a disjoint 565-float result slice: seven public values
// followed by device scratch. No input or runtime aggregate is copied privately.
#define COMBAT_INPUT_WORDS 2146
#define COMBAT_OUTPUT_WORDS 565
StructuredBuffer<uint> commands;
RWStructuredBuffer<float> results;
struct CombatModel {
 uint input,output; int ne;
 float C(int k){return asfloat(commands[input+1+k]);}
 float E(int k){return asfloat(commands[input+221+k]);}
 float Env(int k){return asfloat(commands[input+2141+k]);}
[noinline] void buffs(float t,int who,uint b){
 [loop] for(int k=0;k<NS;k++)results[output+b+(k)]=C(who*CS+20+k);
 [loop] for(int i=0;i<ne;i++)if((int)E(i*ES+3)==0 && results[output+7+(i)]>0 && results[output+167+(i)]>t-1e-8f && ((int)E(i*ES+1)&(1<<who)))results[output+b+((int)E(i*ES+2))]+=E(i*ES+6)*results[output+7+(i)];
}
[noinline] float hit(int base,uint b,float coeff,int normal,int full,int charged,int flags){
 float attack=hi(C(base+0)*(1+results[output+b+(0)]/100)+results[output+b+(1)]-hi(Env(1)*(1+results[output+b+(2)]/100)+results[output+b+(3)],0)*(1-results[output+b+(4)]/100),0);
 float crit=lo(.15f+(results[output+b+(5)]+(normal?results[output+b+(22)]:0))/100,1)*hi(.5f+(results[output+b+(6)]+(normal?results[output+b+(23)]:0))/100,0);
 float core=normal && Env(2)>0?lo(1,pow(Env(2)/hi(C(base+13)*(1-.00908f*results[output+b+(21)]),1),2.55f)):0;
 float bonus=1+crit+(full?.5f:0)+(normal&&C(base+14)>.5f?.3f:0)+core*((C(base+12)-100+results[output+b+(7)])/100);
 float charge=charged?C(base+9)/100*(1+results[output+b+(9)]/100)+results[output+b+(8)]/100:1;
 float extra=results[output+b+(10)]+((flags&1)?results[output+b+(13)]:0)+((flags&2)?results[output+b+(14)]:0)+((flags&4)?results[output+b+(15)]:0)+((flags&8)?results[output+b+(16)]:0);
 float damage=coeff*(normal?1+results[output+b+(11)]/100:1)/100*attack*bonus*charge*(1+extra/100)*(1+results[output+b+(12)]/100)*(C(base+15)>.5f?1.1f+results[output+b+(17)]/100:1);
 return hi(roundDamage(damage),1);
}
[noinline] void event(float t,int ev,int who,int count,int full,int castmask){
 [loop] for(int j=0;j<ne;j++){
  int owner=(int)E(j*ES+(0)),kind=(int)E(j*ES+(3)),timing=(int)E(j*ES+(4));
  if(timing!=ev || (ev!=0&&ev!=1&&ev!=2&&ev!=3&&ev!=10&&owner!=who))continue;
  if(ev==3 && !(castmask&(1<<owner)))continue;
  if((ev==5||ev==6||ev==10) && (count<=0 || count%(int)E(j*ES+(5))))continue;
  if((int)E(j*ES+(9))==1&&!full || (int)E(j*ES+(9))==2&&full)continue;
  if(kind==0){results[output+7+(j)]=lo(results[output+7+(j)]+1,E(j*ES+(8)));results[output+167+(j)]=E(j*ES+(7))<0?1e30f:t+E(j*ES+(7));}
  else if(kind==1){uint b=517;buffs(t,owner,b);results[output+487+(owner)]+=hit(owner*CS,b,E(j*ES+(6)),0,full,0,(int)E(j*ES+(10)))*E(j*ES+(11));}
 }
}
[noinline] void run(){
 int totalshots=0,cycles=0;float fbend=-1,burstnext=3;int castmask=0;
 [loop] for(int j=0;j<ME;j++){results[output+7+(j)]=0;results[output+167+(j)]=-1;results[output+327+(j)]=j<ne?E(j*ES+5):0;}
 [loop] for(int i=0;i<5;i++){results[output+487+(i)]=0;results[output+492+(i)]=C(i*CS+7);results[output+497+(i)]=0;results[output+502+(i)]=C(i*CS+2);results[output+507+(i)]=0;results[output+512+(i)]=0;}
 event(0,0,0,0,0,0);
 [loop] for(int i=0;i<5;i++){uint b=517;buffs(0,i,b);results[output+502+(i)]=(int)hi(1,C(i*CS+2)*(1+results[output+b+(18)]/100));}
 int frames=(int)(Env(0)*60+.00001f);
 [loop] for(int frame=0;frame<frames;frame++){
  float t=frame/60.0f;int full=int(t<fbend);
  if(!full && fbend>=0){event(t,2,0,0,0,castmask);fbend=-1;}
  if(!full && t+1e-8f>=burstnext){
   int chosen[3]={-1,-1,-1};
   [loop] for(int stage=1;stage<=3;stage++)[loop] for(int i=0;i<5;i++)if((int)C(i*CS+16)==stage&&results[output+497+(i)]<=t+1e-8f){if(Env(4)==i+1&&(cycles+1)%3!=0)continue;chosen[stage-1]=i;break;}
   if(chosen[0]>=0&&chosen[1]>=0&&chosen[2]>=0){
    cycles++;castmask=0;[loop] for(int s=0;s<3;s++){int i=chosen[s];castmask|=1<<i;results[output+497+(i)]=t+C(i*CS+17);}
    // CDR is applied to the selected cooldowns, once per matching effect.
    event(t,3,0,0,0,castmask);
    [loop] for(int j=0;j<ne;j++)if((int)E(j*ES+3)==2&&((int)E(j*ES+4)==1||((int)E(j*ES+4)==3&&(castmask&(1<<(int)E(j*ES)))))){[loop] for(int i=0;i<5;i++)if((int)E(j*ES+1)&(1<<i))results[output+497+(i)]-=E(j*ES+6);}
    fbend=t+10;full=1;burstnext=fbend+2;
    event(t,1,0,0,full,castmask);
   }
  }
  [loop] for(int j=0;j<ne;j++)if((int)E(j*ES+4)==4&&t+1e-8f>=results[output+327+(j)]){
   // Isolate this periodic effect without firing other periods.
   // Read the isolated periodic row directly; no local record copy.
   if(!((int)E(j*ES+(9))==1&&!full || (int)E(j*ES+(9))==2&&full)){
    if((int)E(j*ES+(3))==0){results[output+7+(j)]=lo(results[output+7+(j)]+1,E(j*ES+(8)));results[output+167+(j)]=E(j*ES+(7))<0?1e30f:t+E(j*ES+(7));}
    else if((int)E(j*ES+(3))==1){int owner=(int)E(j*ES+(0));uint b=517;buffs(t,owner,b);results[output+487+(owner)]+=hit(owner*CS,b,E(j*ES+(6)),0,full,0,(int)E(j*ES+(10)))*E(j*ES+(11));}
   }
   results[output+327+(j)]+=E(j*ES+5);
  }
  [loop] for(int i=0;i<5;i++){
   if(results[output+492+(i)]>t+1e-8f)continue;
   uint b=541;buffs(t,i,b);
   int cap=(int)hi(1,C(i*CS+(2))*(1+results[output+b+(18)]/100));
   if(results[output+502+(i)]<=0){results[output+502+(i)]=cap;results[output+512+(i)]=0;event(t,8,i,0,full,castmask);}
   results[output+487+(i)]+=hit(i*CS,b,C(i*CS+(1))/C(i*CS+(10)),1,full,int(C(i*CS+(7))>0),0)*C(i*CS+(10))*C(i*CS+(11));
   results[output+502+(i)]--;results[output+507+(i)]++;totalshots++;results[output+512+(i)]++;
   event(t,5,i,(int)results[output+507+(i)],full,castmask);
   event(t,6,i,(int)(results[output+507+(i)]*C(i*CS+(10))*C(i*CS+(11))),full,castmask);
   event(t,10,i,totalshots,full,castmask);
   if(C(i*CS+(7))>0)event(t,9,i,0,full,castmask);
   float interval=C(i*CS+(7))>0?hi(C(i*CS+(19)),C(i*CS+(7))*hi(1-results[output+b+(20)]/100,.01f)+C(i*CS+(8))):1/hi(C(i*CS+(4))+(C(i*CS+(5))-C(i*CS+(4)))*lo(results[output+512+(i)]/hi(C(i*CS+(6)),1),1),.01f);
   if(results[output+502+(i)]<=0){event(t,7,i,0,full,castmask);interval+=hi(C(i*CS+(3))*(1-results[output+b+(19)]/100),.05f);}
   results[output+492+(i)]=t+interval;
  }
 }
 [loop] for(int i=0;i<5;i++)results[output+i]=results[output+487+i];
 results[output+5]=float(totalshots);results[output+6]=float(cycles);
}
};
[shader("compute")]
[numthreads(1,1,1)]
void optimizerCombat(uint3 id:SV_DispatchThreadID){
 if(id.x>=commands[0])return;
 CombatModel m;
 m.input=1+id.x*COMBAT_INPUT_WORDS;m.output=id.x*COMBAT_OUTPUT_WORDS;
 m.ne=int(commands[m.input]);
 m.run();
}
