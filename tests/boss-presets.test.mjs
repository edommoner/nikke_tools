import test from 'node:test';
import assert from 'node:assert/strict';
import {groupPresets} from '../web/enemy-model.mjs';
import {validPreset} from '../web/roster-model.mjs';
import {makePhase} from '../web/phase-model.mjs';
test('different live boss inputs cannot be grouped under equal scalar settings',()=>{
 const settings={'enemy-def':31784,'enemy-code':'풍압',level:400,duration:60,core:0,distance:30};
 const phase=makePhase({id:'core',kind:'core',value:6}),base={mode:'solo',settings,label:'boss'};
 const rows=[{...base,id:'one',patterns:[phase]},{...base,id:'two',patterns:[{...phase,delay:2}]},{...base,id:'three',patterns:[structuredClone(phase)]}];
 const groups=groupPresets(rows,'solo');assert.equal(groups.length,2);assert.equal(groups[0].members.length,2);assert.deepEqual(groups[0].patterns,[phase]);
 assert.ok(validPreset(rows[0]));assert.equal(validPreset({...base,patterns:[{kind:'core',delay:NaN}]}),false);
});
