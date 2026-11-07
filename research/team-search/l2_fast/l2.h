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
// L2FT v3 retains v2, then appends v3 switches; per character: raw reference
// phase seconds[2], per-group burst-state-count flag, per-buff observed-self
// flag. v3 bits: phase-normalized burst occupancy=16, own conditions=32,
// burst-state-gated hit counts=64. v1/v2 never enter those code paths.
// Optional v3 trailing tag128 then one nonnegative bound per buff amount;
// zero means unbounded. Old v3 tables remain readable. Switch128 enables
// plain, nonstacking effect bounds derived at the actual profiling skill level.
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

// Canonical order is ascending table index. Partitions own first-position
// offsets modulo partitions. stride selects lexicographic subset rank % stride
// == 0 for explicitly sampled benchmarks; stride=1 is exhaustive.
struct L2Entry { uint32_t ids[5]; double score; };
struct L2Counts { uint64_t visited, covered, scored; double seconds; };
extern "C" int l2_enumerate(const void* table,const uint32_t* roster,size_t n,
    size_t k,uint32_t partition,uint32_t partitions,uint32_t stride,
    L2Entry* output,size_t* output_count,L2Counts* counts);
// Balanced worker partition: lexicographic (first,second) prefix ordinal
// modulo partitions. The original first-index API remains available above.
extern "C" int l2_enumerate_balanced(const void* table,const uint32_t* roster,size_t n,
    size_t k,uint32_t partition,uint32_t partitions,uint32_t stride,
    L2Entry* output,size_t* output_count,L2Counts* counts);
// Native threads and the WASM runner use balanced partitions.
extern "C" int l2_enumerate_threads(const void* table,const uint32_t* roster,
    size_t n,size_t k,uint32_t threads,uint32_t stride,L2Entry* output,
    size_t* output_count,L2Counts* counts);
