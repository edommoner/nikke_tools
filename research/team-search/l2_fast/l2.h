#pragma once
#include <cstddef>
#include <cstdint>
// L2FT v1 payload: [version,nchars,nkeys,duration,compensated_sum], then
// character: 15 scalars (cycle mask,literal B3,CD,squad id/truth,weapon,class,
// code,charge,ref casts,ref phase0/1,group/buff/dependency counts).
// group: phase,flag bits,unit,coeff,ATK,DEF,core,core bonus,charge multiplier,
//        own[nkeys],base[7],self[7].
// buff: phase,burst dependent,amount/rule counts; (key,value)*; (op,a,b,limit)*.
// dependency: enabled,team,ratio. Trailing metadata is outside this payload.
// L2FT v2 retains those records (payload version=2), then appends:
// switches, action-key indices[7]; per character: base ATK/HP/DEF,
// ranking-own ATK%/flat, rate, charge base, post-fire delay, clips, ammo,
// reload, minimum cycle, charged, literal B1; per group: reference action
// rate, context unit, cast-scaled flag and action-eligible flag; per buff: structural condition; mechanic count,
// then (kind,event,condition,threshold,value,all-allies-scope,max-trigger)*.
// Switch bits: action rate=1, event burst cycle=2, dynamic recipients=4,
// alternate context cadence=8. Version 1 has no extension and no switches.
extern "C" {
void* l2_create(const double* words, size_t count);
void l2_destroy(void* table);
// Distinct in-range character indices; returns -1 on invalid input.
int l2_score_many(const void* table,const uint32_t* squads,size_t count,double* totals,double* members);
void* alloc(size_t bytes);
void release(void* p);
}
// Deterministic xorshift32 streaming workload; seed must be nonzero. Rejection
// sampling of distinct ordered members, optionally requiring cycle coverage.
extern "C" uint32_t l2_generate(const void* table,uint32_t seed,uint32_t* squads,size_t count,int covered);
