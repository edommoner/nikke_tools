#include "binary64.slang"
#include "core_probability.slang"
#include "portable_schema.slang"

StructuredBuffer<uint> commands;
RWStructuredBuffer<uint> results;
static const uint64_t ONE = uint64_t(0x3ff00000) << 32;
static const uint64_t HUNDRED = uint64_t(0x40590000) << 32;
static const uint64_t FOREVER = uint64_t(0x46293e59) << 32 | 0x39a08cea;
static const uint64_t END_EPS = uint64_t(0x3eb0c6f7) << 32 | 0xa0b5ed8d;
static const uint64_t END_BEFORE = uint64_t(0x3f1a36e2) << 32 | 0xeb1c432d;

uint64_t loadNumber(uint at) { return uint64_t(commands[at]) | uint64_t(commands[at+1]) << 32; }
void storeNumber(uint at, uint64_t value) { results[at] = uint(value); results[at+1] = uint(value >> 32); }
uint64_t smaller(uint64_t a, uint64_t b) { return f64Less(a,b) ? a : b; }
uint64_t larger(uint64_t a, uint64_t b) { return f64Less(a,b) ? b : a; }

struct Definition
{
    uint owner, kind, stat, name, maxStack;
    int budget;
    uint64_t value, duration, interval;
    uint immediate, preserve, event, threshold, countMode;
    int eventName, targetName;
    uint forceMask, recipients, target, stageArg, stageOverride, reentry, toggle;
};
struct Frame
{
    uint mode, event, owner, cursor, target;
    int argument;
    uint64_t time;
};
struct Runtime
{
    Definition defs[32];
    int modeIndex[5];
    uint modeEpoch[5], appliedEpoch[5], modeShots[5], pendingReentry[5], reentrySlot, reentryDone, casts[5], burstTraceCount;
    uint pellets[5], muzzles[5], inputBase;
    uint64_t modeEnd[5], reentryDelay;
    uint combatStarted, combat, targetCount, target, aim[5], targetAlive[8], targetGeneration[8], targetHits[8];
    uint64_t targetHP[8], targetDamage[8], targetDefense[8];
    uint timerTarget[32];
    uint weaponEnabled[5], weaponMode[5], capacity[5], ammo[5], shots[5], stage[5], charging[5];
    uint phase, castMask, traceMode, traceTotal, burstTraceTotal, nextFrame, frameCount;
    uint64_t coefficient[5], interval[5], reloadTime[5], chargeTime[5], gain[5], cooldown[5];
    uint64_t nextShot[5], reloadUntil[5], ready[5], chargeUntil[5], gauge, action, fullEnd;
    uint count, error, timerClock, entryClock, traceCount, maxDepth, generation;
    uint activations[32], counters[32], stacks[32], alive[32], entryOrder[32];
    uint timerActive[32], timerEpoch[32], timerOrder[32], timerGeneration[32];
    uint64_t due[32], expiry[32], end[32], total[5], baseAttack[5];
    uint64_t defense, probability, coreBonus, baseCrit, baseCritDamage;
};
struct Sum { uint64_t total; uint64_t correction; };
void addSum(inout Sum sum, uint64_t term)
{
    uint64_t combined = f64Add(sum.total,term);
    uint64_t correction = !f64Less(f64Abs(sum.total),f64Abs(term)) ?
        f64Add(f64Add(sum.total,combined ^ F64_SIGN),term) : f64Add(f64Add(term,combined ^ F64_SIGN),sum.total);
    sum.correction = f64Add(sum.correction,correction); sum.total = combined;
}
uint64_t readStat(inout Runtime s, uint who, uint key, uint64_t when)
{
    Sum sum = {}; sum.total = key == 5 ? s.baseCrit : 0;
    uint previous = 0;
    for (uint pass = 0; pass < s.count; pass++)
    {
        uint next = 0xffffffff, selected = s.count;
        for (uint j = 0; j < s.count; j++)
            if (s.entryOrder[j] > previous && s.entryOrder[j] < next) { next = s.entryOrder[j]; selected = j; }
        if (selected == s.count) break;
        previous = next; Definition d = s.defs[selected];
        if (d.kind != 0 || d.stat != key || s.alive[selected] == 0 || !f64Less(when,s.end[selected]) || (d.recipients & (1U << who)) == 0) continue;
        uint64_t value = f64Mul(d.value, f64FromI64(s.stacks[selected]));
        if (key == 5) value = f64Div(value,HUNDRED);
        if (key == 5 || key == 6) addSum(sum,value); else sum.total = f64Add(sum.total,value);
    }
    uint64_t result = f64Add(sum.total,sum.correction);
    return key == 5 ? larger(0,smaller(ONE,result)) : result;
}

bool targetLive(inout Runtime s, uint target, uint generation)
{
    return s.combat == 0 || (target < s.targetCount && s.targetAlive[target] != 0 && s.targetGeneration[target] == generation);
}
uint aimedTarget(inout Runtime s, uint who)
{
    uint t = s.aim[who];
    if (s.targetAlive[t] != 0) return t;
    for (uint j = 0; j < s.targetCount; j++) if (s.targetAlive[j] != 0) return j;
    return 0xffffffff;
}
void land(inout Runtime s, uint who, uint target, uint64_t amount)
{
    if (s.combat != 0 && s.targetHits[target] == 0x7fffffff) { s.error = 2; return; }
    s.total[who] = f64Add(s.total[who],amount);
    if (s.combat == 0) return;
    s.targetDamage[target] = f64Add(s.targetDamage[target],amount);
    s.targetHP[target] = larger(0,f64Add(s.targetHP[target],amount ^ F64_SIGN));
    s.targetHits[target]++;
    if (f64Zero(s.targetHP[target])) s.targetAlive[target] = 0;
}

// End the old session before callbacks. A child may install a new session.
void clearMode(inout Runtime s, uint who, uint64_t when)
{
    s.modeIndex[who] = -1; s.modeEpoch[who]++; s.appliedEpoch[who] = s.modeEpoch[who];
    s.ammo[who] = s.capacity[who]; s.reloadUntil[who] = F64_SIGN | ONE;
    s.charging[who] = 0; s.nextShot[who] = when; s.modeShots[who] = 0;
}

void pushFrame(inout Runtime s, inout Frame frames[32], inout int depth, uint mode, uint event, uint owner, int argument, uint64_t when)
{
    if (depth == 31) { s.error = 1; return; }
    depth++;
    Frame f = {}; f.mode = mode; f.event = event; f.owner = owner; f.argument = argument; f.time = when;
    uint inherited = event < 32 ? P_TARGET_INHERIT_0 : P_TARGET_INHERIT_1;
    f.target = s.combat == 0 || mode != 0 || (event < 64 && (inherited & (1U << (event%32))) != 0) ? s.target : 0;
    frames[depth] = f; s.maxDepth = max(s.maxDepth,uint(depth+1));
}

void registerTimer(inout Runtime s, uint row, uint64_t when)
{
    Definition d = s.defs[row]; bool was = s.timerActive[row] != 0;
    uint target = d.target != 0 ? 0 : s.target;
    bool sameTarget = s.combat == 0 || (s.timerTarget[row] == target && s.timerGeneration[row] == s.targetGeneration[target]);
    bool preserve = d.kind == 3 && d.preserve != 0 && was && sameTarget;
    if (!preserve)
    {
        if (s.timerEpoch[row] == 0x7fffffff) { s.error = 2; return; }
        s.timerEpoch[row]++;
        s.due[row] = f64Add(when,d.kind == 3 && d.immediate != 0 ? 0 : d.interval);
        s.timerTarget[row] = d.target != 0 ? 0 : s.target;
        s.timerGeneration[row] = s.combat != 0 ? s.targetGeneration[s.timerTarget[row]] : s.generation;
    }
    if (!was)
    {
        if (s.timerClock == 0x7fffffff) { s.error = 2; return; }
        s.timerOrder[row] = ++s.timerClock;
    }
    s.timerActive[row] = 1;
    s.expiry[row] = f64Less(d.duration,0) ? FOREVER : f64Add(when,d.duration);
    if (d.kind == 3)
    {
        s.stacks[row] = min(s.stacks[row]+1,d.maxStack);
        s.end[row] = s.expiry[row]; s.alive[row] = 1;
    }
}

uint64_t damageValue(inout Runtime s, uint who, uint64_t coefficient, uint64_t when, bool normal, uint64_t coreBonus)
{
    uint64_t attack = larger(0,f64Add(f64Mul(s.baseAttack[who],f64Add(ONE,f64Div(readStat(s,who,0,when),HUNDRED))),(s.combat != 0 ? s.targetDefense[s.target] : s.defense) ^ F64_SIGN));
    uint64_t crit = f64Mul(readStat(s,who,5,when),larger(0,f64Add(s.baseCritDamage,f64Div(readStat(s,who,6,when),HUNDRED))));
    uint64_t fullBonus = s.combat != 0 && s.phase == 5 ? uint64_t(0x3fe00000) << 32 : 0;
    uint64_t bonus = f64Add(f64Add(f64Add(ONE,crit),fullBonus),f64Mul(normal ? s.probability : 0,coreBonus));
    uint64_t raw = f64Mul(f64Mul(f64Div(coefficient,HUNDRED),attack),bonus);
    uint status; uint64_t rounded = f64ToI64(raw,0,status);
    if (status != 0) { s.error = 16; return 0; }
    return larger(ONE,f64FromI64(rounded));
}

// Synchronous depth-first dispatch. Parent cursor commits before child push.
// Modes: notification, direct activation, compiled forced-slot selection.
void dispatch(inout Runtime s, uint mode, uint event, uint owner, int argument, uint64_t when, uint output)
{
    uint entryTarget = s.target;
    Frame frames[32]; int depth = -1;
    pushFrame(s,frames,depth,mode,event,owner,argument,when);
    uint work = 0;
    while (depth >= 0 && s.error == 0)
    {
        if (++work > 4096) { s.error = 4; break; }
        Frame f = frames[depth]; s.target = f.target; uint row = s.count;
        if (f.mode == 1)
        {
            if (f.cursor == 0 && f.argument >= 0 && uint(f.argument) < s.count) row = uint(f.argument);
            frames[depth].cursor++;
        }
        else
        {
            while (frames[depth].cursor < s.count)
            {
                uint j = frames[depth].cursor++; Definition d = s.defs[j];
                if (f.mode == 2)
                {
                    if ((s.defs[f.argument].forceMask & (1U << j)) != 0) { row = j; break; }
                    continue;
                }
                if ((f.event != 26 && d.owner != f.owner) || d.event != f.event || ((f.event == 49 || f.event == 29) && d.eventName != f.argument) || (f.event == 4 && d.stageArg != uint(f.argument))) continue;
                if (d.countMode != 0 || f.event == 7 || f.event == 8)
                {
                    if (s.counters[j] == 0x7fffffff || d.threshold == 0) { s.error = 2; break; }
                    s.counters[j]++;
                    if (s.counters[j] % d.threshold != 0) continue;
                }
                row = j; break;
            }
        }
        if (row == s.count) { depth--; continue; }
        Definition d = s.defs[row];
        if (f.mode == 2)
        { pushFrame(s,frames,depth,1,47,d.owner,int(row),f.time); continue; }
        if (f.event != 28)
        {
            if (d.budget >= 0 && s.activations[row] >= uint(d.budget)) continue;
            if (s.activations[row] == 0x7fffffff) { s.error = 2; break; }
            s.activations[row]++;
        }
        if (!f64Zero(d.interval) && f.event != 28) { registerTimer(s,row,f.time); continue; }
        if (d.kind == 0 || d.kind == 4)
        {
            bool live = s.alive[row] != 0 && f64Less(f.time,s.end[row]);
            if (!live) { s.stacks[row] = 0; s.entryOrder[row] = ++s.entryClock; }
            s.stacks[row] = min(s.stacks[row]+1,d.maxStack); s.alive[row] = 1;
            s.end[row] = f64Less(d.duration,0) ? FOREVER : f64Add(f.time,d.duration);
        }
        else if (d.kind == 25) s.pendingReentry[d.owner] = 1;
        else if (d.kind == 2)
        {
            int prior = s.modeIndex[d.owner];
            if (d.toggle != 0 && prior >= 0 && s.defs[prior].name == d.name)
            { clearMode(s,d.owner,f.time); pushFrame(s,frames,depth,0,29,d.owner,int(d.name),f.time); }
            else
            {
                if (prior != int(row)) { s.modeEpoch[d.owner]++; s.modeShots[d.owner] = 0; }
                s.modeIndex[d.owner] = int(row);
                s.modeEnd[d.owner] = f64Less(d.duration,0) ? FOREVER : f64Add(f.time,d.duration);
            }
        }
        else if (d.kind == 1)
        {
            int mode = s.modeIndex[d.owner];
            if (s.combat != 0 && mode >= 0 && s.defs[mode].name == uint(d.targetName))
            { uint name = s.defs[mode].name; clearMode(s,d.owner,f.time); pushFrame(s,frames,depth,0,29,d.owner,int(name),f.time); }
            for (uint j = 0; j < s.count; j++) if (s.defs[j].owner == d.owner && s.defs[j].name == uint(d.targetName))
            { s.alive[j] = 0; s.stacks[j] = 0; s.timerActive[j] = 0; }
        }
        else if (d.kind == 33) pushFrame(s,frames,depth,2,0,d.owner,int(row),f.time);
        else if (d.kind == 3)
        {
            uint target = d.target != 0 ? 0 : f.target;
            uint generation = s.combat != 0 ? s.targetGeneration[target] : s.generation;
            if (!targetLive(s,target,generation)) continue;
            s.target = target;
            if (f.event != 28) s.stacks[row] = 1;
            uint64_t amount = damageValue(s,d.owner,f64Mul(d.value,f64FromI64(s.stacks[row])),f.time,false,s.coreBonus);
            if (s.error != 0) break;
            land(s,d.owner,target,amount);
            if (s.traceTotal == 0x7fffffff) { s.error = 2; break; }
            s.traceTotal++;
            if (s.traceMode == 0) { pushFrame(s,frames,depth,0,49,d.owner,int(d.name),f.time); continue; }
            if (s.traceCount == P_TRACE) { s.error = 8; break; }
            uint at = output + P_TRACE_BASE + s.traceCount++*P_TRACE_WORDS;
            results[at] = row; storeNumber(at+1,f.time); results[at+3] = s.timerEpoch[row];
            results[at+4] = generation; results[at+5] = uint(depth+1); storeNumber(at+6,s.due[row]);
            pushFrame(s,frames,depth,0,49,d.owner,int(d.name),f.time);
        }
        else s.error = 32;
    }
    s.target = entryTarget;
}

void timerPass(inout Runtime s, uint64_t when, bool damagePass, uint output)
{
    uint rows[32], epochs[32], count = 0;
    // Snapshot registration order AND epoch before any child is run.
    for (uint j = 0; j < s.count; j++) if (s.timerActive[j] != 0 && (s.defs[j].kind == 3) == damagePass)
    {
        uint at = count++;
        while (at > 0 && s.timerOrder[j] < s.timerOrder[rows[at-1]])
        { rows[at] = rows[at-1]; epochs[at] = epochs[at-1]; at--; }
        rows[at] = j; epochs[at] = s.timerEpoch[j];
    }
    for (uint pass = 0; pass < count && s.error == 0; pass++)
    {
        uint j = rows[pass]; Definition d = s.defs[j];
        if (s.timerActive[j] == 0 || s.timerEpoch[j] != epochs[pass]) continue;
        if (damagePass && !targetLive(s,s.timerTarget[j],s.timerGeneration[j])) { s.timerActive[j] = 0; continue; }
        uint64_t limit = f64Add(s.expiry[j], d.immediate != 0 ? END_EPS ^ F64_SIGN : END_EPS);
        bool expired = damagePass ? f64Less(limit,s.due[j]) : !f64Less(when,s.expiry[j]);
        if (expired) { s.timerActive[j] = 0; continue; }
        if (f64Less(when,s.due[j])) continue;
        uint64_t observed = damagePass && !f64Less(when,s.expiry[j]) ? f64Add(s.expiry[j],END_BEFORE ^ F64_SIGN) : when;
        s.due[j] = f64Add(s.due[j],d.interval); // Commit before nested callbacks.
        uint parentTarget = s.target; s.target = s.timerTarget[j];
        dispatch(s,1,28,d.owner,int(j),observed,output); s.target = parentTarget;
    }
}
void tick(inout Runtime s, uint64_t when, uint output)
{
    timerPass(s,when,true,output);
    for (uint j = 0; j < s.count; j++) if (s.alive[j] != 0 && !f64Less(when,s.end[j]))
    { s.alive[j] = 0; s.stacks[j] = 0; }
    if (s.combat != 0) for (uint who = 0; who < 5 && s.error == 0; who++)
        if (s.modeIndex[who] >= 0 && !f64Less(when,s.modeEnd[who]))
        { uint name = s.defs[s.modeIndex[who]].name; clearMode(s,who,when); dispatch(s,0,29,who,int(name),when,output); }
    timerPass(s,when,false,output);
}

#include "combat_runtime.slang"

[shader("compute")]
[numthreads(1,1,1)]
void portableEvents(uint3 id : SV_DispatchThreadID)
{
    if (id.x >= commands[0]) return;
    uint input = 1 + id.x*P_INPUT_WORDS, output = id.x*P_OUTPUT_WORDS;
    Runtime s = {}; s.generation = 1; s.count = commands[input+1]; s.combat = commands[input+3]; s.inputBase = input; s.traceMode = commands[input+5];
    if (commands[input] != PORTABLE_ABI || s.count == 0 || s.count > P_DEFINITIONS || commands[input+2] > P_COMMANDS || s.traceMode > 1)
    { results[output] = 64; return; }
    for (uint i = 0; i < 5; i++) s.baseAttack[i] = loadNumber(input+8+2*i);
    s.defense = loadNumber(input+18); s.coreBonus = loadNumber(input+22);
    s.baseCrit = loadNumber(input+24); s.baseCritDamage = loadNumber(input+26);
    if (s.combat != 0) initializeCombat(s,input);
    if (s.error != 0) { results[output] = s.error; return; }
    uint numericStatus; s.probability = coreProbability(loadNumber(input+20),numericStatus);
    if (numericStatus != 0) { results[output] = 128; return; }
    for (uint j = 0; j < s.count; j++)
    {
        uint at = input+P_DEFINITION_BASE+j*P_DEFINITION_WORDS; Definition d;
        d.owner = commands[at+D_OWNER]; d.kind = commands[at+D_KIND]; d.stat = commands[at+D_STAT];
        d.name = commands[at+D_NAME]; d.maxStack = commands[at+D_MAX_STACK]; d.budget = int(commands[at+D_BUDGET]);
        d.value = loadNumber(at+D_VALUE); d.duration = loadNumber(at+D_DURATION); d.interval = loadNumber(at+D_INTERVAL);
        d.immediate = commands[at+D_IMMEDIATE]; d.preserve = commands[at+D_PRESERVE];
        d.event = commands[at+D_EVENT]; d.threshold = commands[at+D_THRESHOLD]; d.countMode = commands[at+D_COUNT_MODE];
        d.eventName = int(commands[at+D_EVENT_NAME]); d.targetName = int(commands[at+D_TARGET_NAME]);
        d.stageArg = commands[at+D_STAGE_ARG]; d.stageOverride = commands[at+D_STAGE_OVERRIDE];
        d.reentry = commands[at+D_REENTRY]; d.toggle = commands[at+D_TOGGLE];
        d.target = commands[at+D_TARGET]; d.forceMask = commands[at+D_FORCE_MASK]; d.recipients = commands[at+D_RECIPIENTS];
        if (d.owner >= 5) { s.error = 64; break; } s.defs[j] = d;
    }
    uint queries = 0;
    for (uint step = 0; step < commands[input+2] && s.error == 0; step++)
    {
        uint at = input+P_COMMAND_BASE+step*8, op = commands[at]; uint64_t when = loadNumber(at+1);
        if (op == 4 && s.combat != 0 && s.combatStarted == 0)
        { s.combatStarted = 1; teamNotify(s,0,when,output); }
        if (s.combat == 0 || op == 4) tick(s,when,output);
        if (s.error != 0) break;
        if (op == 0) dispatch(s,0,commands[at+3],commands[at+4],int(commands[at+5]),when,output);
        else if (op == 4 && s.combat != 0) { squadFrame(s,when,output); s.frameCount++; }
        else if (op == 24 && s.combat != 0) advanceCombat(s,when,output);
        else if ((op == 20 || op == 21 || op == 22) && s.combat != 0)
        {
            uint target = commands[at+5], who = commands[at+4];
            if (target >= s.targetCount || who >= 5) { s.error = 64; break; }
            if (op == 20) { s.aim[who] = target; s.target = target; }
            else if (op == 22) s.targetAlive[target] = 0;
            else
            {
                if (s.targetGeneration[target] == 0x7fffffff) { s.error = 2; break; }
                s.targetGeneration[target]++; s.targetAlive[target] = 1; s.targetHP[target] = loadNumber(at+6);
            }
        }
        else if (op == 18)
        {
            uint who = commands[at+4];
            if (who >= 5) { s.error = 64; break; }
            uint target = s.combat != 0 ? aimedTarget(s,who) : 0;
            if (target == 0xffffffff) continue;
            s.target = target;
            uint64_t amount = damageValue(s,who,loadNumber(at+5),when,true,s.coreBonus);
            if (s.error != 0) break;
            land(s,who,target,amount);
            dispatch(s,0,8,who,0,when,output);
        }
        else if (op == 2)
        {
            uint index = commands[at+6];
            if (index >= P_COMMANDS) { s.error = 64; break; }
            queries = max(queries,index+1); uint dst = output+P_QUERY_BASE+index*P_QUERY_WORDS;
            storeNumber(dst,when);
            for (uint who = 0; who < 5; who++) { storeNumber(dst+2+2*who,s.total[who]); storeNumber(dst+16+2*who,readStat(s,who,0,when)); }
            uint mask = 0; for (uint j = 0; j < s.count; j++) if (s.timerActive[j] != 0) mask |= 1U << j;
            if (s.combat != 0) writeCombatQuery(s,output+P_COMBAT_QUERY_BASE+index*P_COMBAT_QUERY_WORDS,output+P_COMBAT_STATE_QUERY_BASE+index*P_COMBAT_STATE_QUERY_WORDS);
            results[dst+12] = mask; results[dst+13] = s.combat != 0 ? s.targetGeneration[s.target] : s.generation; results[dst+14] = 0; results[dst+15] = s.timerClock;
        }
        else s.error = 64;
    }
    for (uint j = 0; j < s.count; j++)
    {
        uint at = output+P_STATE_BASE+j*10; storeNumber(at,s.due[j]); storeNumber(at+2,s.expiry[j]);
        results[at+4] = s.timerEpoch[j]; results[at+5] = s.timerOrder[j]; results[at+6] = s.timerActive[j];
        results[at+7] = s.stacks[j]; results[at+8] = s.activations[j];
        results[output+P_TIMER_TARGET_BASE+j*2] = s.timerTarget[j];
        results[output+P_TIMER_TARGET_BASE+j*2+1] = s.timerGeneration[j];
    }
    if (s.combat != 0) for (uint j = 0; j < s.targetCount; j++)
    {
        uint dst = output+P_TARGET_STATE_BASE+j*10;
        results[dst] = s.targetGeneration[j]; results[dst+1] = s.targetAlive[j];
        storeNumber(dst+2,s.targetHP[j]); storeNumber(dst+4,s.targetDamage[j]); results[dst+6] = s.targetHits[j];
    }
    results[output] = s.error; results[output+1] = queries; results[output+2] = s.traceCount; results[output+3] = s.maxDepth; results[output+4] = s.burstTraceCount; results[output+6] = s.traceTotal;
    results[output+7] = s.burstTraceTotal; results[output+8] = s.frameCount;
}
