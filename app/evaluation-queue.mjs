// Shared cache and ordered batch boundary for both direct and job evaluations.
export function createEvaluator({worker,keyOf,cache=new Map(),limit=300,cacheable=()=>true}) {
  const validate=body=>{
    if(!['cpu','cuda_detail','metal_detail','cuda_shared_detail'].includes(body.compute_backend||'cpu'))throw Error('未対応の詳細計算方法です。');
    if(body.verify_detail!==undefined&&typeof body.verify_detail!=='boolean')throw Error('CPU照合の指定が不正です。');
  };
  const save=(key,result,enabled)=>{
    result.compute ||= {requested:'cpu',backend:'cpu'};
    if(!enabled)return {...result,cache_hit:false};
    if(cache.size>=limit)cache.delete(cache.keys().next().value);
    cache.set(key,structuredClone(result));return {...result,cache_hit:false};
  };
  async function cpuFallback(body,job,error){
    const result=await worker({...body,action:'evaluate'},job);
    result.compute={requested:body.compute_backend,backend:'cpu',fallback_reason:'GPUを実行できなかったため、CPUで詳細計算しました。',error:error.message};
    return result;
  }
  async function many(bodies,job){
    if(bodies.length>32)throw Error('一度に計算できる候補は32件です。');
    const rows=new Array(bodies.length),pending=new Map();
    for(const [index,body]of bodies.entries()){
      try{
        validate(body);const enabled=cacheable(body),key=enabled?keyOf(body):Symbol();
        if(cache.has(key)){rows[index]={result:{...structuredClone(cache.get(key)),cache_hit:true}};continue;}
        if(!pending.has(key))pending.set(key,{key,body,indices:[],cacheable:enabled});
        pending.get(key).indices.push(index);
      }catch(error){rows[index]={error:error.message};}
    }
    const entries=[...pending.values()];
    const publish=(entry,row)=>{
      const value=row.error?row:{result:save(entry.key,row.result,entry.cacheable)};
      for(const index of entry.indices)rows[index]=structuredClone(value);
    };
    // Each fresh worker owns a bounded batch; Python groups compatible wires
    // while keeping every original row and its CPU comparison independent.
    const shared=new Map();
    for(const entry of entries.filter(e=>['metal_detail','cuda_shared_detail'].includes(e.body.compute_backend))){
      const backend=entry.body.compute_backend;
      if(!shared.has(backend))shared.set(backend,[]);
      shared.get(backend).push(entry);
    }
    const batches=[entries.filter(e=>e.body.compute_backend==='cuda_detail')];
    for(const group of shared.values())for(let i=0;i<group.length;i+=8)batches.push(group.slice(i,i+8));
    for(let i=batches.length-1;i>=0;i--)if(!batches[i].length)batches.splice(i,1);
    for(const gpu of batches){
      let outputs;
      try{
        const action=gpu[0].body.compute_backend==='cuda_detail'?'evaluate_detail_batch':'evaluate_portable_detail_batch';
        outputs=await worker({action,evaluations:gpu.map(e=>e.body)},job);
        if(!Array.isArray(outputs)||outputs.length!==gpu.length||outputs.some(r=>!r||!(typeof r.error==='string'||r.result&&typeof r.result==='object')))throw Error('GPUの計算結果の形式が不正です。');
      }catch(error){
        outputs=[];
        for(const entry of gpu){
          try{
            if(!error.gpuUnavailable||job?.status==='cancelled')throw error;
            outputs.push({result:await cpuFallback(entry.body,job,error)});
          }catch(failure){outputs.push({error:failure.message});}
        }
      }
      gpu.forEach((entry,i)=>publish(entry,outputs[i]));
    }
    for(const entry of entries.filter(e=>!['cuda_detail','metal_detail','cuda_shared_detail'].includes(e.body.compute_backend))){
      try{publish(entry,{result:await worker({...entry.body,action:'evaluate'},job)});}
      catch(error){publish(entry,{error:error.message});}
    }
    return rows;
  }
  async function one(body,job){const [row]=await many([body],job);if(row.error)throw Error(row.error);return row.result;}
  return {one,many,isCached:body=>cache.has(keyOf(body))};
}

export async function advanceCases(job,evaluator){
  while(job.index<job.cases.length&&job.status==='running'){
    let items,rows;
    if(job.pendingGpuResults){
      const pending=job.pendingGpuResults;
      items=job.cases.slice(job.index,job.index+pending.rows.length);
      if(pending.index!==job.index||JSON.stringify(items.map(item=>item.evaluation))!==pending.inputs)throw Error('一時停止中に計算候補が変更されました。');
      rows=pending.rows;delete job.pendingGpuResults;
    }else{
      const first=job.cases[job.index],backend=first.evaluation.compute_backend;
      const cap=backend==='cuda_detail'?32:['metal_detail','cuda_shared_detail'].includes(backend)?8:1;
      let count=1;
      if(cap>1&&!evaluator.isCached(first.evaluation)){
        while(count<cap&&job.index+count<job.cases.length&&job.cases[job.index+count].evaluation.compute_backend===backend)count++;
      }
      items=job.cases.slice(job.index,job.index+count);
      const inputs=JSON.stringify(items.map(item=>item.evaluation));
      rows=await evaluator.many(items.map(item=>item.evaluation),job);
      if(JSON.stringify(items.map(item=>item.evaluation))!==inputs)throw Error('計算中に候補が変更されました。');
    }
    if(job.status==='cancelled'){delete job.pendingGpuResults;break;}
    for(let i=0;i<items.length;i++){
      const item=items[i],row=rows[i];
      if(row.error){
        if(job.kind!=='optimize')throw Error(row.error);
        job.results.push({value:item.value,error:row.error});
      }else{
        const result=row.result;
        job.results.push({value:item.value,field:item.field,result,meets:job.target?(job.strict?result.total_damage>job.target:result.total_damage>=job.target):null});
      }
      job.index++;job.updatedAt=Date.now();
      if(job.pauseRequested){
        if(i+1<items.length)job.pendingGpuResults={index:job.index,inputs:JSON.stringify(items.slice(i+1).map(item=>item.evaluation)),rows:rows.slice(i+1)};
        job.status='paused';break;
      }
    }
  }
}
