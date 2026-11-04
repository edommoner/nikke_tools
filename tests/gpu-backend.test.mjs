import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {runInNewContext} from 'node:vm';

const lines=readFileSync(new URL('../web/app.js',import.meta.url),'utf8').split('\n');
function sourceLine(prefix){
 const matches=lines.filter(line=>line.startsWith(prefix));
 assert.equal(matches.length,1);
 return matches[0];
}
const helper=sourceLine('function defaultDetailBackend(');
const demo=sourceLine("for(const id of ['demo-gpu','demo-gpu-start'])");
const initializer=sourceLine("guarded(async()=>{const hardware=await api('/api/hardware')");

test('default detail backend follows CUDA, Metal, shared CUDA, CPU priority',()=>{
 for(let mask=0;mask<8;mask++){
  const hardware={available:!!(mask&4),metal:{available:!!(mask&2)},shared_cuda:{available:!!(mask&1)}};
  const expected=mask&4?'cuda_verified':mask&2?'metal_detail':mask&1?'cuda_shared_detail':'cpu';
  assert.equal(runInNewContext(helper+'\ndefaultDetailBackend(hardware)',{hardware}),expected);
 }
 for(const hardware of [{},{available:false},{metal:null,shared_cuda:null}]){
  assert.equal(runInNewContext(helper+'\ndefaultDetailBackend(hardware)',{hardware}),'cpu');
 }
});

const cases=[
 ['CUDA',{available:true,metal:{available:true},shared_cuda:{available:true}},'cuda_verified','GPU詳細＋CPU照合'],
 ['Metal',{available:false,metal:{available:true},shared_cuda:{available:true}},'metal_detail','Metal詳細＋CPU照合'],
 ['shared CUDA',{available:false,metal:{available:false},shared_cuda:{available:true}},'cuda_shared_detail','共通CUDA詳細＋CPU照合'],
 ['CPU',{available:false},'cpu',null],
];
for(const [name,availability,backend,label] of cases){
 test(`${name}: both demo buttons and page initialization select the expected backend`,async()=>{
  const hardware={...availability,reason:'legacy CUDA unavailable'},nodes=new Map(),pending=[],calls=[],notices=[];
  const $=id=>{if(!nodes.has(id))nodes.set(id,{querySelector:selector=>$(id+'/'+selector)});return nodes.get(id);};
  const data={profile:{chars:{}}};
  const context={$,Promise,api:async url=>{
   calls.push(url);
   if(url==='/api/hardware')return hardware;
   assert.equal(url,'/api/demo?gpu_detail=true');return data;
  },guarded:fn=>(...args)=>{const result=fn(...args);pending.push(result);return result;},
  requireEditable(){},setImport:value=>assert.equal(value,data),setView:value=>assert.equal(value,'single'),renderBoard(){},notice:text=>notices.push(text)};
  runInNewContext(helper+'\n'+initializer,context);
  await Promise.all(pending);
  assert.equal($('detail-backend').value,backend);
  assert.deepEqual(calls,['/api/hardware']);
  assert.equal($('detail-backend/[value="metal_detail"]').disabled,!hardware.metal?.available);
  assert.equal($('detail-backend/[value="cuda_shared_detail"]').disabled,!hardware.shared_cuda?.available);
  for(const value of ['cuda_detail','cuda_verified'])assert.equal($(`detail-backend/[value="${value}"]`).disabled,!hardware.available);
  runInNewContext(demo,context);
  for(const id of ['demo-gpu','demo-gpu-start']){
   calls.length=0;$('detail-backend').value='stale';
   await $(id).onclick();
   assert.equal($('detail-backend').value,backend);
   assert.deepEqual(calls,['/api/demo?gpu_detail=true','/api/hardware']);
   const notice=notices.at(-1);
   if(label){
    assert.ok(notice.includes(label));assert.match(notice,/GPU詳細用の架空育成を読み込みました/);
    assert.match(notice,/「この部隊を計算」.*GPU.*CPUと照合/);assert.doesNotMatch(notice,/GPUを使用できません/);
   }else assert.equal(notice,'GPUを使用できません：legacy CUDA unavailable。デモはCPUで計算できます。');
  }
 });
}
