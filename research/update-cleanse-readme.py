from pathlib import Path
p=Path(__file__).resolve().parents[1]/'README.md';s=p.read_text(encoding='utf-8')
s=s.replace('現在のコンパイル受理は113／203人、宝ものを含む監査は443／812条件です。','v18時点のコンパイル受理は113／203人、宝ものを含む監査は443／812条件でした。')
s=s.replace('GPU受理が11から113キャラ（再突入拡張前は110キャラ）','GPU受理が11から116キャラ（デバフ解除拡張前は113キャラ）')
s=s.replace('`research/detail-coverage-before.json`／`research/detail-coverage-burst-stage.json`','`research/detail-coverage-before.json`／`research/detail-coverage-cleanse.json`')
s=s.replace('現時点の受理は443条件','現時点の受理は455条件')
p.write_text(s,encoding='utf-8')
