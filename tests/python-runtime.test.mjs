import test from 'node:test';
import assert from 'node:assert/strict';
import {resolvePython} from '../app/python-runtime.mjs';

test('Mac/Linux use python3 and explicit interpreters win on every platform',()=>{
  for(const platform of ['darwin','linux','win32']) {
    assert.equal(resolvePython({platform,env:{NIKKE_PYTHON:'/custom/python'}}),'/custom/python');
    if(platform!=='win32')assert.equal(resolvePython({platform,env:{},exists:()=>true}),'python3');
  }
});

test('Windows keeps its installed bundled Python with a normal python fallback',()=>{
  const options={platform:'win32',env:{USERPROFILE:'C:/task-user'}};
  assert.match(resolvePython({...options,exists:()=>true}),/python\.exe$/);
  assert.equal(resolvePython({...options,exists:()=>false}),'python');
});
