# 複数ownerの実射撃groupと独立Metal検証

sealed `attack-group-mixed` は81入力（native68／拒否13）。旧long60の全入力・正本指紋と251,658,240byteを保持し、実ニヒリスター／ベロータの元の全効果を同じ編成へ入れた20ケースを追加した。宣言listenerやCPU hit listは追加しない。共有CUDA／MetalのSlang本文・数値・Runtime・正本CPU・normalizerは変更していない。

## 確認した範囲

listenerをslot0/1とslot3/4へ配置し、所有bitmap3/24を静的入力から生成する。3秒／30秒はADD1/3体、180秒はADD3体、native／明示all-logical-enemiesの2policyを比較する。Niの閾値2とVelの閾値4をowner別に検査するため、ADD1体の宣言世界ではNiだけ、ADD3体では双方が通知される。native世界は元routerのBODY/ADD選択を変えず、groupなしの元battle全体／全物理shotとも一致させる。

20ケースの計1,116group／528通知について、owner・identity・epoch・時刻・packet数・全typed対象と通知keyのcaster／閾値／対象を照合した。180秒では65件目以降も双方のownerを含む完全履歴を確認する。全battle・ADD別量／hit／世代・global overkill・enemy buff binding・参照解放は既存の共通比較器を使う。既存の物理shot観測は2048 prefixと省略数の契約を維持し、無制限の全shot記録を新しく認定しない。

Apple M5の実Metal1回が全81一致。GPU11.661451秒、pipeline cache必須hitでPSO0.002401秒、Slang新規起動0。CUDA/MSL生成指紋は旧long60と同じ。別processのGPU禁止sealも全81成功した。保存出力の先頭owner、後方slotのowner、通知数、65件目以降のownerの4改変を共通比較器が拒否した。先頭64の二重記録を同時に改変し、単なるprefix不一致だけで検出する実験にはしていない。

## 固定packageと制御検査

元実行はdevelopment packageで行い、独立sealから新しい専用goldenを作成した。旧goldenの書換えや数値差分の除外はない。sealed最終packageはCPU34検査／81入力・native68の事前検査が成功。共通制御392件（Windows専用1skip）が成功した。full2848→compact1567ファイルで、残る全recordとgoldenは一致した。実行済みpackageとの差はsealed registry／共通fixture同梱、compact許可集合、そのテスト、新規goldenと共通JSON fixtureだけ。計算・入力・native／比較コードは同じで、GPU再実行は不要だった。

最初の制御検査では、前ターンのcompiler certificateテストがlong60のfixtureを別suite内でも読むのに、packageへ同梱されていない問題があった。元失敗を保存し、既存の共通fixture whitelistへlong60 goldenとfull-source certificateの2ファイルを明示追加した。テストのskipや検査条件の緩和はしていない。

## 容量不足と損失なし回収

Metal開始前に空き555,769,856byteで容量guardが停止した。入力／出力の必要676,000,000byteと既定1GiB予約を変えず、GPUを開始しなかった。既存疎ファイル化へ `--block-size 4096` を明示opt-inで追加した（既定65536は維持）。filesystemのallocation unitへ整列することを確認し、完全にゼロの範囲だけをF_PUNCHHOLEで解放する。現在のAPFS上の小fixtureで、64KiBごとに非ゼロ4KiBがある場合の回収と全byte／inode／元metadata保持を実証した。

```sh
python scripts/nikke_gpu.py sparsify-raw --capture FINISHED_CAPTURE \
  --out NEW_RECEIPT.json --block-size 4096 --apply
```

元5,070,913,536byte captureから1,246,224,384byte、新339,738,624byte captureから318,083,072byte、計1,564,307,456byteの割当を回収した。rawは元の通常ファイルのままで、各全SHA・全byte・inodeと既存証拠を前後検査した。削除・圧縮置換・GPU再構成は0。失敗・未完了capture、変更中／多重link／不正anchor／不適合blockは引き続き停止する。4KiBの汎用filesystem対応を認定したものではない。

全体は静的245/266、base185/203、残20model gap／全キャラ認定0／通常UI CPUを維持する。今回のall-logical policyはゲームの空間・爆発範囲の証明ではない。部位／geometry／arena境界／通常producer導入／現在の本体CUDA計算は残件。Windowsは新規実行依頼0で、既存PTXの状態は接続未復旧のためunknown、再依頼しない。詳細checkpointと `research/mixed-attack-group-evidence/` を参照する。
