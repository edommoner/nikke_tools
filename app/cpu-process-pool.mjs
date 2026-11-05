import os from 'node:os';
export const cpuProcessLimit=()=>Math.max(1,os.cpus().length-1);
let active=0;
const waiting=[];
function pump(){
  while(active<cpuProcessLimit()&&waiting.length){
    const {job,run,resolve,reject}=waiting.shift();
    if(job?.status==='cancelled'){resolve(undefined);continue;}
    active++;
    let result;
    try{result=run();}catch(error){active--;reject(error);continue;}
    Promise.resolve(result).then(resolve,reject).finally(()=>{active--;pump();});
  }
}
// One process-wide budget, including concurrent jobs and verification callers.
export function withCpuProcess(job,run){
  return new Promise((resolve,reject)=>{waiting.push({job,run,resolve,reject});pump();});
}
