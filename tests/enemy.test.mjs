import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {enemyScope,groupPresets} from '../web/enemy-model.mjs';
const records=JSON.parse(readFileSync(new URL('../data/raid-presets.json',import.meta.url),'utf8')).presets;
test('enemy contexts are separate for single, solo, and union',()=>{
 assert.equal(enemyScope(true,5),'single');assert.equal(enemyScope(false,5),'solo');assert.equal(enemyScope(false,1),'union');
 const solo=groupPresets(records,'solo'),union=groupPresets(records,'union');
 assert.ok(solo.every(g=>g.members.every(p=>p.mode==='solo')));assert.ok(union.every(g=>g.members.every(p=>p.mode==='union')));
 assert.equal(solo.flatMap(g=>g.members).length,42);assert.equal(union.flatMap(g=>g.members).length,300);
});
test('grouping identical numeric settings preserves all source occurrences',()=>{
 const grouped=groupPresets(records,'single');assert.ok(grouped.length<records.length);
 assert.equal(grouped.flatMap(g=>g.members).length,records.length);
 const keys=grouped.map(g=>JSON.stringify(g.settings));assert.equal(new Set(keys).size,keys.length);
 for(const g of grouped)for(const row of g.members)assert.deepEqual(row.settings,g.settings);
 const one=records.find(p=>p.mode==='solo'),different=structuredClone(one);different.settings.core=10;
 assert.equal(groupPresets([one,different],'solo').length,2);
});
