// The ordinary battle loop owns the single WorldSchedule. Only typed storage
// and bounded receipt/scratch banks are added after its unchanged output prefix.
#define PORTABLE_RESIDENT_RUNTIME
#define PORTABLE_DESTRUCTIBLE_FRAME
#define PORTABLE_DESTRUCTIBLE_BATTLE
#ifndef DT_INPUT
#define DT_INPUT(s,offset) ((s).inputBase+104400+(offset))
#define DT_OUTPUT(output,offset) ((output)+786432+(offset))
#endif
#define DF_DESCRIPTOR(s) DT_INPUT(s,5120)
#define DF_EXTRA(s) DT_INPUT(s,0)
#define DF_BASE(output) DT_OUTPUT(output,1024)
#define DF_HEADER(output) DT_OUTPUT(output,2816)
#define DF_SCHEDULE(s,w,extra,output) WorldSchedule w=frameSchedule(s);
#define DF_SCRATCH(output,depth) (DT_OUTPUT(output,153568)+uint(depth)*544)
#ifndef DF_VALID
#define DF_VALID(s,d,descriptor) (commands[descriptor+3]==0x44425431U&&(d.damageFlags&~(H_NAMED_SKILL|524288U))==0)
#endif
#define DF_HAS_SAMPLE(s,row) destructibleActivationHasTargets(s,row)
#define DF_COEFF(s,scratch,output,value) dtStore(scratch+532,value);
#define DF_AMOUNT(s,scratch,output,value) dtStore(scratch+534,value);
#define DF_SELECTION(s,scratch,output,selected,f,d) destructibleBattleCapture(s,scratch,selected,f,d);
#define DF_RECEIPT(s,scratch,output,cursor) (results[scratch+530]+16+(cursor)*8)
#define DF_ATTACK_ID(s,scratch,descriptor) results[scratch+531]
#define DF_COMPLETE(s,scratch) if(results[scratch+531]!=0) results[results[scratch+530]+10]=1;
#define DF_ROW_ENABLED(s,row) ((row)<(s).count&&commands[DT_INPUT(s,5424)+(row)]!=0)
#define DF_BODY_FALLBACK(s,row) (commands[DT_INPUT(s,5424)+(row)]>=3)
#define DF_MATCH(s,row,at,selected) (results[at+3]!=0&&(DF_BODY_FALLBACK(s,row)?((selected)==0&&(results[at]==3||(commands[DT_INPUT(s,5424)+(row)]==4&&results[at]==4))&&results[at+10]==commands[DT_INPUT(s,5681)]&&results[at+11]==commands[DT_INPUT(s,5682)]&&results[at+12]==commands[DT_INPUT(s,5683)]):results[at]==2))
