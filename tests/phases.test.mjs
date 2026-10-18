import test from 'node:test';
import assert from 'node:assert/strict';
import {makePhase,editablePhase,normalizePatterns} from '../web/phase-model.mjs';
test('repeat phases use real lifecycle references and round-trip the editing fields',()=>{
 for(const kind of ['core','move'])for(const repeat of [false,true]){
  const input={id:'test',kind,wait:3,duration:5,value:6,repeat},p=makePhase(input);
  assert.deepEqual(editablePhase(p),input);
  assert.deepEqual(p.after,repeat?['start','test']:['start']);assert.equal(p.repeat,repeat?0:1);
 }
});
test('complex imports are retained without flattening dependencies or emissions',()=>{
 const input=[{id:'a',kind:'core',core_px:6,after:[{node:'b',outcome:'followed'}],until:{after:[{node:'c',delay:.3}]},emit:['event:target_spawn']}];
 const copy=normalizePatterns(input);assert.deepEqual(copy,input);copy[0].after[0].node='changed';assert.equal(input[0].after[0].node,'b');assert.equal(editablePhase(input[0]),null);
});
test('invalid editor values and non-JSON inputs fail instead of changing numeric meaning',()=>{
 for(const override of [{wait:-1},{duration:0},{duration:Infinity},{value:.5},{repeat:1}])assert.throws(()=>makePhase({id:'a',kind:'core',...override}));
 for(const value of [[{kind:'core',core_px:NaN}],[{kind:'core',extra:undefined}],Array(129).fill({kind:'idle'}),[null]])assert.throws(()=>normalizePatterns(value));
});
