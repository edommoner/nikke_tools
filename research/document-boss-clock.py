from pathlib import Path
p=Path(__file__).resolve().parents[1]/'README.md';s=p.read_text(encoding='utf-8')
needle='## 詳細GPU版の実装・CPU照合\n\n'
insert='''ボスのコア出現・距離／適正武器の変更を、開始条件・終了条件・繰り返し・イベント通知までGPU側で判断する処理（v31）を追加しました。CPUで作った行動履歴をGPUへ渡す方式ではありません。通常画面の「詳細条件 → コア出現・距離変更を設定」から追加でき、プリセット・画面別の敵条件・保存JSONに保持します。コアを出し入れする場合は基本のコア径を0にします。結果では「ボス行動の開始・終了を見る」を展開できます。

GPUで対応するボス行動はcore／move／idle／groggyです。ボス行動は32件、各行動の依存先・通知は8件、各行動の終了履歴は512件、全体ログは4,096件までです。上限超過や未対応のボス行動は結果を採用せず、通常画面では理由付きでCPUへ切り替えます。ABIは`detail_boss_clock_v31`、1部隊のGPU作業領域は639,072バイトです。座標による命中、個別パーツの移動、敵からの攻撃・遮蔽物・戦闘不能などは未対応です。収録済みレイドプリセットに、この新しい行動データを自動補完する変更ではありません。

'''
assert needle in s;s=s.replace(needle,needle+insert,1);p.write_text(s,encoding='utf-8')
p=p.parent/'web/index.html';s=p.read_text(encoding='utf-8').replace('非公式ファンツール · 静止ボス / 選択した射撃運用 / 期待値で計算','非公式ファンツール · 設定したボス条件 / 選択した射撃運用 / 期待値で計算');p.write_text(s,encoding='utf-8')
