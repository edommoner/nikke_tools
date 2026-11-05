import {createHash} from 'node:crypto';
import os from 'node:os';
import {bestDisjoint} from './optimizer.mjs';

export const verificationWorkers=()=>Math.max(1,os.cpus().length-1);
export const candidateKey=body=>JSON.stringify(body.squad);
export const isSampled=(id,key)=>createHash('sha256').update(id+key).digest()[0]<32;
export const pending=result=>result?.compute?.cpu_verification?.status==='pending';
const squadKey=result=>JSON.stringify(result.members.map(m=>m.name));

// Optimizer UI renders only recommendation.teams, in two identical panels.
export function displayedRows(job){
  const keys=new Set(job.incumbent?.teams.map(t=>JSON.stringify(t.squad))||[]);
  return job.results.filter(r=>r.result&&keys.has(squadKey(r.result)));
}
export function recompute(job){
  // Keep a valid GPU-selected combination, but refresh its scores after CPU fixes.
  const teams=job.incumbent?.teams.map(t=>job.results.find(r=>r.result&&squadKey(r.result)===JSON.stringify(t.squad))?.result);
  job.incumbent=teams?.every(Boolean)?{damage:teams.reduce((n,r)=>n+r.total_damage,0),teams:teams.map(r=>({squad:r.members.map(m=>m.name),damage:r.total_damage}))}:null;
  const found=bestDisjoint(job.results,job.teamCount,job.groups);
  if(found&&(!job.incumbent||found.damage>job.incumbent.damage))job.incumbent=found;
}
export function recommendationForView(job){
  if(job.kind!=='optimize')return job.incumbent||null;
  if(job.verification?.escalated&&job.results.some(r=>pending(r.result)))return null;
  if(job.incumbent?.teams.some(t=>!job.results.some(r=>r.result&&!pending(r.result)&&squadKey(r.result)===JSON.stringify(t.squad))))return null;
  return job.incumbent||null;
}
export function verificationView(job){
  if(job.kind!=='optimize')return undefined;
  const v=job.verification;
  return {policy:'displayed+sample',sample_rate:1/8,sampled:v?.sampled.size||0,displayed:v?.displayed.size||0,
    verified:job.results.filter(r=>r.result&&!pending(r.result)).length,mismatches:v?.mismatches||0,escalated:v?.escalated||false,...(v?.reason?{reason:v.reason}:{})};
}
export async function verifyOptimizer(job,evaluator,{concurrency=verificationWorkers()}={}){
  if(job.kind!=='optimize'||job.status==='cancelled')return;
  const width=Math.min(verificationWorkers(),Math.max(1,Number.isFinite(concurrency)?Math.floor(concurrency):1));
  const v=job.verification ||= {sampled:new Set(),displayed:new Set(),mismatches:0,escalated:false};
  const successful=job.results.flatMap((row,index)=>row.result?[{row,body:job.cases[index].evaluation}]:[]);
  const sampled=successful.filter(r=>isSampled(job.id,candidateKey(r.body)));
  if(!sampled.length&&successful.length)sampled.push(successful[0]);
  sampled.forEach(r=>v.sampled.add(candidateKey(r.body)));
  const rejected=successful.filter(r=>r.row.result.compute?.gpu_result_rejected);
  if(rejected.length){
    v.mismatches=rejected.length;v.escalated=true;
    v.reason='共有カーネルとCPUの結果に差があったため全候補のCPU照合へ切り替えました。';
  }
  async function check(entries,kind){
    let cursor=0,failure;
    const todo=entries.filter(r=>pending(r.row.result));
    await Promise.all(Array.from({length:Math.min(width,todo.length)},async()=>{
      while(cursor<todo.length&&job.status!=='cancelled'&&!failure){
        // One row is a small batch: fresh Python process per CPU comparison.
        const entry=todo[cursor++],wrapper={body:entry.body,result:entry.row.result};
        try{
          const checks=await evaluator.verify([wrapper],job);
          if(job.status==='cancelled')return;
          entry.row.result=wrapper.result;
          entry.row.result.compute.verification_kind=kind;
          if(checks.some(c=>!c.matched)){
            v.mismatches+=checks.filter(c=>!c.matched).length;
            v.escalated=true;v.reason='共有カーネルとCPUの結果に差があったため全候補のCPU照合へ切り替えました。';
          }
        }catch(error){failure=error;}
      }
    }));
    if(failure)throw failure;
  }
  job.phase='表示する部隊をCPUで照合中';
  try{
    await check(sampled,'sample');
    while(job.status!=='cancelled'){
      if(v.escalated)await check(successful,'full');
      if(job.status==='cancelled')return;
      recompute(job);
      const displayed=displayedRows(job);
      displayed.forEach(r=>v.displayed.add(squadKey(r.result)));
      const entries=successful.filter(r=>displayed.includes(r.row));
      if(!entries.some(r=>pending(r.row.result)))break;
      await check(entries,'displayed');
    }
  }finally{job.phase=null;}
}
