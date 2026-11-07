import test from 'node:test';
import assert from 'node:assert/strict';
import {makeHistoryEntry,pushHistory,formatHistoryLabel,openStore,getItem,setItem,deleteItem} from '../web/storage-model.mjs';

const snapshot = (name='a') => ({profile:{chars:{[name]:{level:100}}},squad:[name],is_demo:false});
const entry = (name, now='2026-11-05T01:02:03Z', source='file') => makeHistoryEntry({snapshot:snapshot(name),source,now});

test('history entry captures import metadata and an independent snapshot',()=>{
  const original=snapshot(),result=makeHistoryEntry({snapshot:original,source:'blablalink',now:'2026-11-05T01:02:03Z'});
  assert.equal(typeof result.id,'string');assert.ok(result.id);
  assert.equal(result.imported_at,'2026-11-05T01:02:03.000Z');
  assert.equal(result.source,'blablalink');assert.equal(result.is_demo,false);assert.equal(result.owned_count,1);
  assert.deepEqual(result.snapshot,original);assert.equal(result.label,formatHistoryLabel(result));
  original.profile.chars.a.level=200;assert.equal(result.snapshot.profile.chars.a.level,100);
  assert.equal(makeHistoryEntry({snapshot:{...snapshot(),is_demo:true},source:'session'}).is_demo,true);
});

test('history pushes newest imports first without modifying the original list',()=>{
  const older=entry('a'),newer=entry('b','2026-11-06T01:02:03Z'),list=[older];
  assert.deepEqual(pushHistory(list,newer),[newer,older]);assert.deepEqual(list,[older]);
});

test('history retains the most recent 20 imports and supports an explicit limit',()=>{
  let list=[];for(let i=0;i<25;i++)list=pushHistory(list,entry(String(i)));
  assert.equal(list.length,20);assert.ok(list[0].snapshot.profile.chars['24']);assert.ok(list[19].snapshot.profile.chars['5']);
  assert.equal(pushHistory(list,entry('new'),3).length,3);assert.deepEqual(pushHistory(list,entry('new'),0),[]);
});

test('identical consecutive profiles refresh the timestamp without adding an entry',()=>{
  const older=entry('a'),newer=entry('a','2026-11-06T01:02:03Z','session');newer.snapshot.squad=[];
  const result=pushHistory([older],newer);
  assert.equal(result.length,1);assert.equal(result[0].id,older.id);assert.equal(result[0].imported_at,newer.imported_at);
  assert.equal(older.imported_at,'2026-11-05T01:02:03.000Z');
  const different=entry('b');assert.equal(pushHistory([different,older],newer).length,3);
});

test('history labels include local date-time, Japanese source labels and owned count',()=>{
  for(const [source,label] of [['blablalink','BlaBlaLink'],['file','JSONファイル'],['session','保存ファイル']]){
    const result=entry('a',undefined,source),text=formatHistoryLabel(result);
    assert.ok(text.includes(new Date(result.imported_at).toLocaleString('ja-JP')));
    assert.ok(text.includes(label));assert.ok(text.includes('所持人数：1人'));
  }
});

test('IndexedDB helpers resolve to fallbacks when IndexedDB is unavailable',async()=>{
  const descriptor=Object.getOwnPropertyDescriptor(globalThis,'indexedDB');
  try{
    Object.defineProperty(globalThis,'indexedDB',{configurable:true,value:undefined});
    assert.equal(await openStore(),null);assert.equal(await getItem('current-session'),null);
    assert.equal(await setItem('current-session',{}),false);assert.equal(await deleteItem('import-history'),false);
  }finally{if(descriptor)Object.defineProperty(globalThis,'indexedDB',descriptor);else delete globalThis.indexedDB;}
});

test('IndexedDB helpers resolve to fallbacks when opening throws',async()=>{
  const descriptor=Object.getOwnPropertyDescriptor(globalThis,'indexedDB');
  try{
    Object.defineProperty(globalThis,'indexedDB',{configurable:true,value:{open(){throw Error('denied');}}});
    assert.equal(await openStore(),null);assert.equal(await getItem('current-session'),null);
    assert.equal(await setItem('current-session',{}),false);assert.equal(await deleteItem('import-history'),false);
  }finally{if(descriptor)Object.defineProperty(globalThis,'indexedDB',descriptor);else delete globalThis.indexedDB;}
});

test('demo imports never enter history or replace a real import',()=>{
  const real=entry('a'),demo=makeHistoryEntry({snapshot:{...snapshot('a'),is_demo:true},source:'session'});
  assert.deepEqual(pushHistory([],demo),[]);
  assert.deepEqual(pushHistory([real],demo),[real]);
  const first=entry('b');assert.deepEqual(pushHistory(null,first),[first]);
});

test('IndexedDB writes succeed only when the transaction commits, and quota aborts resolve false',async()=>{
  const descriptor=Object.getOwnPropertyDescriptor(globalThis,'indexedDB');
  let fail=false,closed=0,stored=new Map();
  const db={close(){closed++;},transaction(name,mode){
    assert.equal(name,'kv');
    const transaction={objectStore(){return {
      get(key){const request={};queueMicrotask(()=>{request.result=stored.get(key);transaction.oncomplete();});return request;},
      put(value,key){const request={};queueMicrotask(()=>{if(fail)transaction.onabort();else{stored.set(key,structuredClone(value));transaction.oncomplete();}});return request;},
      delete(key){const request={};queueMicrotask(()=>{stored.delete(key);transaction.oncomplete();});return request;}
    };}};
    assert.ok(['readonly','readwrite'].includes(mode));return transaction;
  }};
  try{
    Object.defineProperty(globalThis,'indexedDB',{configurable:true,value:{open(){const request={};queueMicrotask(()=>{request.result=db;request.onsuccess();});return request;}}});
    assert.equal(await setItem('history',{a:1}),true);
    assert.deepEqual(await getItem('history'),{a:1});
    fail=true;assert.equal(await setItem('history',{a:2}),false);
    assert.deepEqual(await getItem('history'),{a:1});
    assert.equal(await deleteItem('history'),true);assert.equal(await getItem('history'),null);
    assert.equal(closed,6);
  }finally{if(descriptor)Object.defineProperty(globalThis,'indexedDB',descriptor);else delete globalThis.indexedDB;}
});

test('IndexedDB blocked opens and transaction creation failures are harmless',async()=>{
  const descriptor=Object.getOwnPropertyDescriptor(globalThis,'indexedDB');
  try{
    Object.defineProperty(globalThis,'indexedDB',{configurable:true,value:{open(){const request={};queueMicrotask(()=>request.onblocked());return request;}}});
    assert.equal(await getItem('history'),null);assert.equal(await setItem('history',[]),false);
    let closed=0;
    Object.defineProperty(globalThis,'indexedDB',{configurable:true,value:{open(){const request={};queueMicrotask(()=>{request.result={close(){closed++;},transaction(){throw Error('denied');}};request.onsuccess();});return request;}}});
    assert.equal(await getItem('history'),null);assert.equal(await setItem('history',[]),false);assert.equal(closed,2);
  }finally{if(descriptor)Object.defineProperty(globalThis,'indexedDB',descriptor);else delete globalThis.indexedDB;}
});
