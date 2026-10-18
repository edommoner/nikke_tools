"""One-shot integration of authored parts into ordinary enemy controls."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def edit(file,old,new):
 p=ROOT/file;t=p.read_text(encoding='utf-8');assert t.count(old)==1,(file,old[:70],t.count(old));p.write_text(t.replace(old,new),encoding='utf-8')
edit('server.mjs',"'/enemy-model.mjs':'enemy-model.mjs'","'/enemy-model.mjs':'enemy-model.mjs','/parts-model.mjs':'parts-model.mjs'")
edit('web/app.js',"import {enemyScope,groupPresets}","import {normalizeParts,reachLabels} from '/parts-model.mjs';\nimport {enemyScope,groupPresets}")
edit('web/app.js','customPresets:[],enemyContexts:{},scores:{}','customPresets:[],enemyContexts:{},enemyParts:[],scores:{}')
edit('web/app.js',"distance:num('distance')}};}","distance:num('distance'),parts:normalizeParts(state.enemyParts)}};}")
edit('web/app.js',"$('open-battle').onclick=()=>openDialog('battle-dialog');","$('open-battle').onclick=()=>{renderParts();openDialog('battle-dialog');};")
edit('web/app.js',"function computeDetails(result){","function computeDetailsCore(result){")
anchor='function computeDetailsCore(result){'
helpers='''function computeDetails(result){const parts=result.parts_state||[];return computeDetailsCore(result)+(parts.length?`<details class="parts-result"><summary>パーツの命中・破壊結果を見る（${parts.length}個）</summary><table><thead><tr><th>パーツ</th><th>追加ダメージ</th><th>命中</th><th>状態</th></tr></thead><tbody>${parts.map(p=>`<tr><td>${e(p.name)}</td><td>${fmt(p.damage)}</td><td>${fmt(p.hits)}</td><td>${p.destroyed?`${p.destroyed_at}秒で破壊`:'未破壊'}</td></tr>`).join('')}</tbody></table></details>`:'');}
function renderParts(){$('enemy-parts-list').innerHTML=state.enemyParts.map((p,i)=>`<div class="parts-row" data-part-row="${i}"><label>名前<input data-part-field="name" aria-label="パーツ${i+1}の名前" value="${e(p.name)}" maxlength="80"></label><label>HP<input data-part-field="hp" aria-label="パーツ${i+1}のHP" type="number" min="0" max="1000000000000000" value="${p.hp}"></label><label>到達段階<select data-part-field="reach" aria-label="パーツ${i+1}の到達段階">${reachLabels.slice(1).map((text,k)=>`<option value="${k+1}" ${p.reach===k+1?'selected':''}>${k+1} · ${text}</option>`).join('')}</select></label><button class="button text" data-remove-part="${i}" aria-label="パーツ${i+1}を削除">削除</button></div>`).join('');$('add-enemy-part').disabled=state.busy||state.enemyParts.length>=32;}
$('enemy-parts-list').onchange=guarded(event=>{requireEditable();const input=event.target,field=input.dataset.partField;if(!field)return;const i=Number(input.closest('[data-part-row]').dataset.partRow);state.enemyParts[i][field]=field==='name'?input.value:Number(input.value);renderBoard();rememberEnemy(enemyScope(state.singleMode,state.raidCount));});
$('enemy-parts-list').onclick=guarded(event=>{const button=event.target.closest('[data-remove-part]');if(!button)return;requireEditable();state.enemyParts.splice(Number(button.dataset.removePart),1);renderParts();renderBoard();rememberEnemy(enemyScope(state.singleMode,state.raidCount));});
$('add-enemy-part').onclick=guarded(()=>{requireEditable();if(state.enemyParts.length>=32)throw Error('パーツは32個までです。');let i=1;while(state.enemyParts.some(p=>p.name==='パーツ'+i))i++;state.enemyParts.push({name:'パーツ'+i,hp:0,reach:1});renderParts();renderBoard();rememberEnemy(enemyScope(state.singleMode,state.raidCount));});
'''
edit('web/app.js',anchor,helpers+anchor)
edit('web/app.js',"presetId:$('enemy-preset').value};}","presetId:$('enemy-preset').value,parts:clone(state.enemyParts)};}")
edit('web/app.js',"function restoreEnemy(scope){const saved=state.enemyContexts[scope];", "function restoreEnemy(scope){const saved=state.enemyContexts[scope];state.enemyParts=clone(saved?.parts||[]);renderParts();")
edit('web/app.js',"const savedEnemy=state.enemyContexts[enemyScope(state.singleMode,state.raidCount)];", "const savedEnemy=state.enemyContexts[enemyScope(state.singleMode,state.raidCount)];state.enemyParts=normalizeParts(savedEnemy?.parts||raw.enemyParts||[]);renderParts();")
edit('web/app.js',"for(const id of presetFields)$(id).value=preset.settings[id];", "state.enemyParts=normalizeParts(preset.parts||[]);renderParts();for(const id of presetFields)$(id).value=preset.settings[id];")
edit('web/app.js',"label,settings};if(!validPreset(preset))", "label,settings,parts:normalizeParts(state.enemyParts)};if(!validPreset(preset))")
edit('web/app.js',"const data={format:'nikke-tools-session-v1',ui_version:2,", "normalizeParts(state.enemyParts);const data={format:'nikke-tools-session-v1',ui_version:3,enemyParts:clone(state.enemyParts),")
edit('web/roster-model.mjs',"export const elementLabels", "import {validParts} from './parts-model.mjs';\nexport const elementLabels")
edit('web/roster-model.mjs',"const s=p?.settings;return typeof p?.label", "const s=p?.settings;return (p?.parts===undefined||validParts(p.parts))&&typeof p?.label")
markup='''<details id="enemy-parts-editor"><summary>パーツの命中・破壊を設定</summary><p class="subtle">同時に出現する固定パーツを追加できます。HP 0は破壊されない対象です。位置は到達段階で近似し、座標・移動・阻止部位は扱いません。</p><div id="enemy-parts-list"></div><button id="add-enemy-part" class="button ghost">パーツを追加</button></details>'''
edit('web/index.html','<p id="burst-policy-note"',markup+'<p id="burst-policy-note"')
with (ROOT/'web/style.css').open('a',encoding='utf-8') as f:f.write('\n.parts-row{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:12px 0;border-bottom:1px solid var(--line,#354052)}.parts-row label{min-width:0}.parts-row input,.parts-row select{width:100%;box-sizing:border-box}.parts-row label:nth-child(3){grid-column:1/-1}.parts-row button{grid-column:2;justify-self:end}.parts-result{margin:12px 0;overflow:auto}.parts-result table{width:100%;font-size:.8rem}.parts-result th,.parts-result td{padding:6px;text-align:right}.parts-result td:first-child,.parts-result th:first-child{text-align:left}\n')
print('Added ordinary parts controls, scoped restore/presets/export, and per-part results')
