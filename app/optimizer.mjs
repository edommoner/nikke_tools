/** Candidate-pool search. Bounds the work; never claims a global optimum. */
export function candidatePool(characters, count, limit=160, seed=41, templates=[]) {
  let randomState=seed>>>0;
  const rand=()=>{randomState=(1664525*randomState+1013904223)>>>0;return randomState/4294967296;};
  const pool=[],groups=[],seen=new Map();
  for(let attempt=0;attempt<400&&pool.length<limit;attempt++){
    const remaining=[...characters],teams=[];
    const take=(predicate)=>{
      const options=remaining.filter(predicate).sort((a,b)=>b.potential-a.potential).slice(0,Math.max(4,Math.ceil(remaining.length/3)));
      if(!options.length)return null;
      const selected=options[Math.min(options.length-1,Math.floor(rand()**1.6*options.length))];
      remaining.splice(remaining.indexOf(selected),1);return selected.name;
    };
    for(let t=0;t<count;t++){
      const available = new Set(remaining.map(c=>c.name));
      const potential = new Map(remaining.map(c=>[c.name,c.potential]));
      const usable = templates.filter(s=>s.every(n=>available.has(n))).sort((a,b)=>b.reduce((v,n)=>v+potential.get(n),0)-a.reduce((v,n)=>v+potential.get(n),0)).slice(0,8);
      if(usable.length && rand()<0.8){
        const selected=usable[Math.floor(rand()*usable.length)];teams.push([...selected]);
        for(const name of selected)remaining.splice(remaining.findIndex(c=>c.name===name),1);
        continue;
      }
      const team=[];
      for(const stage of ['1','2','3','3']){const n=take(c=>String(c.burst).includes(stage));if(n)team.push(n);else break;}
      if(team.length!==4)break;
      const extra=take(c=>String(c.burst).includes('3'))||take(()=>true);
      if(!extra)break;team.push(extra);teams.push(team);
    }
    if(teams.length!==count)continue;
    const group=[];
    for(const squad of teams){
      const key=JSON.stringify(squad);let index=seen.get(key);
      if(index===undefined){if(pool.length>=limit)break;index=pool.length;seen.set(key,index);pool.push(squad);}
      group.push(index);
    }
    if(group.length===count)groups.push(group);
  }
  if(!groups.length)throw Error(`${count}部隊を構成する候補を作れませんでした。情報不足、使用済み、バースト段階の人数を確認してください。`);
  return {pool,groups};
}
export function bestDisjoint(results,count,groups=[],width=256){
  const candidates=results.map((r,index)=>r.result?({index,squad:r.result.members.map(m=>m.name),score:r.result.total_damage}):null).filter(Boolean);
  const byIndex=new Map(candidates.map(c=>[c.index,c]));
  let best=null;
  for(const group of groups){if(group.every(i=>byIndex.has(i))){const items=group.map(i=>byIndex.get(i)),score=items.reduce((n,c)=>n+c.score,0);if(!best||score>best.score)best={items,score};}}
  let beam=[{items:[],used:new Set(),score:0,last:-1}];
  for(let depth=0;depth<count;depth++){
    const next=[];
    for(const state of beam)for(let i=state.last+1;i<candidates.length;i++){
      const c=candidates[i];if(c.squad.some(n=>state.used.has(n)))continue;
      next.push({items:[...state.items,c],used:new Set([...state.used,...c.squad]),score:state.score+c.score,last:i});
    }
    next.sort((a,b)=>b.score-a.score);beam=next.slice(0,width);
    if(!beam.length)break;
  }
  for(const state of beam)if(state.items.length===count&&(!best||state.score>best.score))best=state;
  return best?{damage:best.score,teams:best.items.map(c=>({squad:c.squad,damage:c.score}))}:null;
}



/** Preserve one complete feasible group before adding the highest GPU estimates.
 * Approximate values only change calculation order; never enter final results.
 */
export function rankCombatPool(pool,groups,scores){
  const byIndex=new Map();
  for(const s of scores){
    if(!Number.isInteger(s.index)||s.index<0||s.index>=pool.length||!Number.isSafeInteger(s.damage)||s.damage<0||JSON.stringify(s.squad)!==JSON.stringify(pool[s.index])||byIndex.has(s.index))throw Error('GPU combat result validation failed');
    byIndex.set(s.index,s.damage);
  }
  if(!byIndex.size)throw Error('GPU combat returned no scores');
  const ranked=[...byIndex.keys()].sort((a,b)=>byIndex.get(b)-byIndex.get(a)||a-b);
  const usable=groups.filter(g=>g.every(i=>byIndex.has(i)));
  usable.sort((a,b)=>b.reduce((n,i)=>n+byIndex.get(i),0)-a.reduce((n,i)=>n+byIndex.get(i),0));
  const first=usable[0]||[];
  return [...new Set([...first,...ranked,...pool.map((_,i)=>i)])];
}
