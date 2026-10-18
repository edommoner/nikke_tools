from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'web/index.html';s=p.read_text(encoding='utf-8');a='<label>射撃運用'
assert a in s
s=s.replace(a,'<label>対象抽選の乱数シード<input id="random-seed" type="number" value="0" min="0" max="4294967295" step="1"></label><p class="subtle">ランダムな味方対象を再現するための番号です。同じ番号でCPUとGPUを比較します。クリティカルなどは期待値で計算します。</p>'+a)
p.write_text(s,encoding='utf-8')
p=ROOT/'web/app.js';s=p.read_text(encoding='utf-8')
s=s.replace("burst_gauge_mode:$('burst-gauge-mode').value,duration:","burst_gauge_mode:$('burst-gauge-mode').value,seed:num('random-seed'),duration:")
s=s.replace("request.burst_gauge_mode||'fixed'", "request.burst_gauge_mode||'fixed',request.seed??0")
s=s.replace("'shooting-policy','burst-gauge-mode'", "'shooting-policy','burst-gauge-mode','random-seed'")
s=s.replace("$('burst-gauge-mode').value=raw.settings?.['burst-gauge-mode']||'fixed';", "$('burst-gauge-mode').value=raw.settings?.['burst-gauge-mode']||'fixed';$('random-seed').value=raw.settings?.['random-seed']??0;")
s=s.replace("$('burst-gauge-mode').value='fixed';$('detail-backend')", "$('burst-gauge-mode').value='fixed';$('random-seed').value=0;$('detail-backend')")
s=s.replace("?'実蓄積':'固定周期'}</p>", "?'実蓄積':'固定周期'} / 対象抽選シード：${current.seed??0}</p>")
p.write_text(s,encoding='utf-8')
print('Random seed control, request identity, stale-result detection and session persistence updated.')
