import {randomUUID,createHash} from 'node:crypto';
import {readFileSync,lstatSync} from 'node:fs';
import path from 'node:path';

export function attachBrowser(job){
  job.browser={request(rows){
    if(job.status==='cancelled')return Promise.reject(Error('計算を終了しました。'));
    if(job.awaitingBrowser)throw Error('ブラウザの計算がすでに進行中です。');
    return new Promise((resolve,reject)=>{
      job.awaitingBrowser={token:randomUUID(),rows};
      job.browserResolve=resolve;job.browserReject=reject;
    }).finally(()=>{delete job.awaitingBrowser;delete job.browserResolve;delete job.browserReject;});
  }};
}
export function cancelBrowser(job){job.browserReject?.(Error('計算を終了しました。'));}
export function acceptBrowserResults(job,body,userAgent=''){
  const request=job.awaitingBrowser;
  if(job.status!=='running'||!request||body?.token!==request.token||!Array.isArray(body.results)||body.results.length!==request.rows.length)throw Error('ブラウザの計算要求が一致しません。');
  if(body.worker_count!==undefined&&(!Number.isInteger(body.worker_count)||body.worker_count<1||body.worker_count>32))throw Error('ブラウザのワーカー数が不正です。');
  const results=body.results.map((r,i)=>{
    if(!r||r.input_sha256!==request.rows[i].wire.input_sha256||typeof r.readback_gzip_base64!=='string'||r.readback_gzip_base64.length>12*1024*1024||!r.readback_gzip_base64.length||r.readback_gzip_base64.length%4!==0||!/^[A-Za-z0-9+/]*={0,2}$/.test(r.readback_gzip_base64)||Buffer.from(r.readback_gzip_base64,'base64').toString('base64')!==r.readback_gzip_base64||!Number.isFinite(r.browser_seconds)||r.browser_seconds<0)throw Error('ブラウザの計算結果が不正です。');
    return {input_sha256:r.input_sha256,readback_gzip_base64:r.readback_gzip_base64,browser_seconds:r.browser_seconds,device:`${String(userAgent).slice(0,440)} · workers=${body.worker_count??'unreported'} (client-reported)`};
  });
  // Consume the token before resolving: a simultaneous replay must fail.
  delete job.awaitingBrowser;job.browserResolve(results);
}
export function browserWasm(root,identity){
  if(!/^[a-f0-9]{64}$/.test(identity))throw Error('Unknown browser wasm identity');
  const directory=path.join(root,'research/portable-build/wasm',identity),file=path.join(directory,'product.wasm');
  if(lstatSync(directory).isSymbolicLink()||lstatSync(file).isSymbolicLink()||lstatSync(path.join(directory,'build.json')).isSymbolicLink())throw Error('Invalid browser wasm cache');
  const receipt=JSON.parse(readFileSync(path.join(directory,'build.json'),'utf8')),raw=readFileSync(file);
  const {sources,compiler_version,flags}=receipt;
  // Match Python's canonical identity serialization; only these build fields participate.
  const canonical=JSON.stringify({compiler_version,flags,sources:Object.fromEntries(Object.entries(sources).sort(([a],[b])=>a.localeCompare(b)))});
  if(receipt.identity!==identity||createHash('sha256').update(canonical).digest('hex')!==identity||createHash('sha256').update(raw).digest('hex')!==receipt.wasm_sha256)throw Error('Invalid browser wasm cache identity');
  return raw;
}
