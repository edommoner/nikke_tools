"""Record accepted production behavior, preserving historical port notes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for p in ['research/detail-heal-sharing-production-verification.json','research/detail-heal-sharing-api-verification.json','research/detail-heal-sharing-browser-verification.json']:
    assert json.loads((ROOT/p).read_text(encoding='utf-8'))['passed'],p
p=ROOT/'README.md';s=p.read_text(encoding='utf-8');needle='## GPU詳細計算 v40';assert needle in s and '## GPU詳細計算 v41' not in s
text='''## GPU詳細計算 v41

回復分配 `heal_split` をGPUに追加しました。レムの通常時/バースト時の重複、ナユタ、外部からの回復、吸血、満タンの対象、期限切れ、戦闘不能/復活、余剰回復保存との組み合わせを扱います。分配量やHP推移をCPUからGPUへ再生する方式ではありません。

固定CPU版には分配がなかったため、`app/heal_sharing_compat.py` で参照モデルを補完しています。対象1人につき有効な分配効果1つを1口として、つながった集団へ口数で分配します。満タンでも取り分を消費し、余った分の再配分はしません。元の回復対象への回復量補正と発動者の与回復補正を分配前に1度適用し、各取り分ではHP変化と保存枠を更新します。追加の回復時通知は出さず、元の回復の通知だけを1回出します。一般的な複数発動者の接続、補正の位置、条件付き分配、配信順序は明示したモデルで、全相互作用の実機検証済みという意味ではありません。[レムの分配口数と満タン対象の説明](https://www.prydwen.gg/nikke/characters/rem)を参考にしています。

追加25ケース（実キャラ5部隊を含む）と既存153ケースを、native/PTX各178ケースでCPU参照モデルと照合しました。部隊合計・5人のダメージ・バースト・HP/遮蔽物・装填/チャージ・両乱数状態・HPイベント順序を比較しています。独立した手計算19ケース、CPU部隊25ケース、過去のCPU合計153ケースも確認しました。入れ子の回復と、レムの6口/8口、ナユタの実分配が発動したことを別に検査しています。

通常版の23テスト（178部隊ケース＋境界17）、Node 26テスト、通常APIとブラウザーのGPU単独/CPU照合も通過しました。架空の所持装備・ヒーリングキューブLv4・スキル7/5/9・一時加算（攻撃12,000、HP100,000、防御250）のレム編成で、変更前94,476,142、変更後98,154,067です。実アカウントの取り込み成功、速度向上、全通常テストの再実行を示すものではありません。

現在のコンパイル対応は161/203体、宝もの段階の文脈は635/812です。全状況での正確性を保証する件数ではありません。ATK基準の回復保存/放出、シールド増幅、被ダメージ分配、敵側効果、座標やCPUモデルの不足などが残っており、全キャラ・全効果GPU化は未完です。検証記録は `research/detail-heal-sharing-checkpoint.json`、通常画面用の架空データは `research/detail-heal-sharing-ui-fixture.json` にあります。

'''
p.write_text(s.replace(needle,text+needle,1),encoding='utf-8')
p=ROOT/'research/boss-gpu-integration-notes.json';r=json.loads(p.read_text(encoding='utf-8'));r['status']='v41 weighted healing sharing: native/PTX178 each, CPU arithmetic19/squads25/historical totals153, production23, API/browser and Node26 passed. Full objective incomplete.'
r['current_boundary']['gpu_compiler']+=' v41 also autonomously distributes healing by live carrier links, including overlapping Rem/Nayuta, body healing/lifesteal and synchronous nested HP events, against an explicit extended CPU reference model.'
r['heal_sharing_checkpoint']=dict(path='research/detail-heal-sharing-checkpoint.json',abi='detail_heal_sharing_v41',objective_complete=False)
r['next_required_work'][0]['requirements'][0]='Continue ATK-based heal_overcharge_store_atk_pct/discharge; healing sharing is implemented under declared model choices, with in-game interaction verification still incomplete.'
r['next_required_work'][1]['requirements'][0]='Attack-attached debuffs, enemy debuff/DOT patterns, cover controls, remaining healing/storage families and all remaining unsupported actual effects.'
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print('Updated v41 production documentation. Full goal incomplete.')
