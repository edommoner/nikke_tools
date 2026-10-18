import test from 'node:test';
import assert from 'node:assert/strict';
import {normalizeParts} from '../web/parts-model.mjs';
import {validPreset} from '../web/roster-model.mjs';
test('part settings preserve unbreakable HP and tier while isolating returned edits',()=>{
 const input=[{name:'装甲',hp:0,reach:2},{name:'砲台',hp:12.5,reach:4}],saved=structuredClone(input),copy=normalizeParts(input);
 assert.deepEqual(copy,input);copy[0].hp=123;assert.deepEqual(input,saved);
 const enemy={def:31784,parts:normalizeParts(input)};assert.notEqual(JSON.stringify(enemy),JSON.stringify({...enemy,parts:[]}));
});
test('invalid parts cannot enter saved enemy presets',()=>{
 const settings={'enemy-def':31784,'enemy-code':'풍압',level:400,duration:60,core:0,distance:30};
 assert.ok(validPreset({label:'部位あり',settings,parts:[{name:'砲台',hp:10,reach:5}]}));
 for(const parts of [[{name:'砲台',hp:10,reach:6}],[{name:'砲台',hp:NaN,reach:1}],[{name:'砲台',hp:10,reach:1,ignored:true}],[{name:'砲台',hp:1,reach:1},{name:'砲台',hp:2,reach:2}],Array.from({length:33},(_,i)=>({name:String(i),hp:0,reach:1}))]){
  assert.throws(()=>normalizeParts(parts));assert.equal(validPreset({label:'部位あり',settings,parts}),false);
 }
});
