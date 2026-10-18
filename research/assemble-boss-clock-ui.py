"""Wire simple editable boss phases into existing enemy contexts and presets."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def edit(name,changes):
    p=ROOT/name;t=p.read_text(encoding='utf-8')
    for a,b in changes:
        assert a in t,(name,a);t=t.replace(a,b)
    p.write_text(t,encoding='utf-8')
edit('web/app.js',[
 ("import {normalizeParts,reachLabels}","import {normalizePatterns,makePhase,editablePhase} from '/phase-model.mjs';\nimport {normalizeParts,reachLabels}"),
 ('enemyParts:[],scores:', 'enemyParts:[],enemyPatterns:[],scores:'),
 ('parts:normalizeParts(state.enemyParts)', 'parts:normalizeParts(state.enemyParts),patterns:normalizePatterns(state.enemyPatterns)'),
 ('parts:clone(state.enemyParts)', 'parts:clone(state.enemyParts),patterns:normalizePatterns(state.enemyPatterns)'),
 ('enemyParts:clone(state.enemyParts)', 'enemyParts:clone(state.enemyParts),enemyPatterns:normalizePatterns(state.enemyPatterns)'),
 ('state.enemyParts=clone(saved?.parts||[]);', 'state.enemyPatterns=normalizePatterns(saved?.patterns||[]);state.enemyParts=clone(saved?.parts||[]);'),
 ('state.enemyParts=normalizeParts(preset.parts||[]);', 'state.enemyPatterns=normalizePatterns(preset.patterns||[]);state.enemyParts=normalizeParts(preset.parts||[]);'),
 ('state.enemyParts=normalizeParts(savedEnemy?.parts||raw.enemyParts||[]);', 'state.enemyPatterns=normalizePatterns(savedEnemy?.patterns||raw.enemyPatterns||[]);state.enemyParts=normalizeParts(savedEnemy?.parts||raw.enemyParts||[]);'),
 ('renderParts();','renderParts();renderPhases();'),
 ('return computeDetailsCore(result)+(parts.length?', 'return computeDetailsCore(result)+bossDetails(result)+(parts.length?'),
 ('function renderParts(){',(ROOT/'research/boss-clock-ui.txt').read_text(encoding='utf-8')+'function renderParts(){'),
])
edit('web/index.html',[
 ('<p id="burst-policy-note"', '<details id="enemy-phase-editor"><summary>コア出現・距離変更を設定</summary><p class="subtle">設定中だけコアが出現、または距離が変わります。終了後は元の値に戻ります。繰り返す場合、開始までの待ち時間を終了後にも挟みます。複数のコアは最大値、距離は後から始まった行動を使います。</p><div id="enemy-phase-list"></div><button id="add-enemy-phase" class="button ghost">ボス行動を追加</button></details><p id="burst-policy-note"'),
 ('ボス固有のギミック・生存・任意の手動操作指定はこの試作の対象外です。','移動・コア以外のボス行動や座標・生存などはGPUで未対応です。未対応の定義では理由を表示してCPUへ切り替えます。'),
])
edit('server.mjs',[("'/parts-model.mjs':'parts-model.mjs'","'/parts-model.mjs':'parts-model.mjs','/phase-model.mjs':'phase-model.mjs'")])
edit('web/roster-model.mjs',[
 ("import {validParts}","import {validPatterns} from './phase-model.mjs';\nimport {validParts}"),
 ("return (p?.parts===undefined||validParts(p.parts))&&", "return (p?.patterns===undefined||validPatterns(p.patterns))&&(p?.parts===undefined||validParts(p.parts))&&"),
])
edit('web/enemy-model.mjs',[
 ("const key=JSON.stringify(presetFields.map(k=>row.settings[k]));", "const scalar=presetFields.map(k=>row.settings[k]);const key=JSON.stringify(row.patterns?.length||row.parts?.length?[scalar,row.parts||[],row.patterns||[]]:scalar);"),
 ("settings:{...row.settings},members:[]", "settings:{...row.settings},...(row.parts?.length?{parts:structuredClone(row.parts)}:{}),...(row.patterns?.length?{patterns:structuredClone(row.patterns)}:{}),members:[]"),
])
p=ROOT/'web/style.css';p.write_text(p.read_text(encoding='utf-8')+'\n.phase-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;padding:12px 0;border-bottom:1px solid var(--border,#35414d)}.phase-row .check{display:flex;align-items:center;gap:8px}.phase-row button{justify-self:end}.boss-details .table-scroll{max-height:340px;overflow:auto}\n',encoding='utf-8')
print('Boss phase UI assembled')
