from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'README.md';text=p.read_text(encoding='utf-8')
anchor='味方HP・防御型の編成条件（v27）'
assert text.count(anchor)==1
assert '部隊共通のパーツ／本体命中通知（v28）' not in text
text=text.replace(anchor,(ROOT/'research/team-hits-doc.txt').read_text(encoding='utf-8')+anchor)
text=text.replace('現行の記録は `research/detail-ally-conditions-verification.json`','v27の記録は `research/detail-ally-conditions-verification.json`')
p.write_text(text,encoding='utf-8')
print('README updated for verified v28 scope and remaining capacity work')
