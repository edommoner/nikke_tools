// Shared cache and ordered batch boundary for both direct and job evaluations.
export function createEvaluator({worker,keyOf,cache=new Map(),limit=300}) {
  const validate=body=>{
    if(!['cpu','cuda_detail','metal_detail','cuda_shared_detail'].includes(body.compute_backend||'cpu'))throw Error('未対応の詳細計算方法です。');
    if(body.verify_detail!==undefined&&typeof body.verify_detail!=='boolean')throw Error('CPU照合の指定が不正です。');
  };
  const save=(key,result)=>{
    result.compute ||= {requested:'cpu',backend:'cpu'};
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
        validate(body);const key=keyOf(body);
        if(cache.has(key)){rows[index]={result:{...structuredClone(cache.get(key)),cache_hit:true}};continue;}
        if(!pending.has(key))pending.set(key,{key,body,indices:[]});
        pending.get(key).indices.push(index);
      }catch(error){rows[index]={error:error.message};}
    }
    const entries=[...pending.values()];
    const publish=(entry,row)=>{
      const value=row.error?row:{result:save(entry.key,row.result)};
      for(const index of entry.indices)rows[index]=structuredClone(value);
    };
    // Shared GPU runs in a fresh worker because preparation uses temporary
    // global aliases. Preserve ordering/cache semantics without a second queue.
    const batches=[entries.filter(e=>e.body.compute_backend==='cuda_detail'),
      ...entries.filter(e=>['metal_detail','cuda_shared_detail'].includes(e.body.compute_backend)).map(e=>[e])].filter(b=>b.length);
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
    const first=job.cases[job.index];let count=1;
    if(first.evaluation.compute_backend==='cuda_detail'&&!evaluator.isCached(first.evaluation)){
      while(count<32&&job.index+count<job.cases.length&&job.cases[job.index+count].evaluation.compute_backend==='cuda_detail')count++;
    }
    const items=job.cases.slice(job.index,job.index+count);
    const rows=await evaluator.many(items.map(item=>item.evaluation),job);
    if(job.status==='cancelled')break;
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
      if(job.pauseRequested){job.status='paused';break;}
    }
  }
}
