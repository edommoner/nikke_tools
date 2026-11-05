# 保留着弾の照会順とHP由来の攻撃力

共有Slangのフルバースト着弾で、正本の「バフ辞書→現在の参照数→HP基準」の照会順を接続した。実際のヒット数は詠唱時の固定値を使う。着弾時に読み直す参照数はその後で固定値に置き換わるため、再度整数化したり256の容量上限で拒否したりしない。詠唱時に固定する上限256は維持する。詠唱1→現在1024でも1ヒットで成功する2契約を追加した。

0ヒット・負の固定ヒット数は、バフ／参照数／HPの必要な照会だけで終了する。ダメージ係数積、整数丸め、部位・迎撃の追加計算、core確率やヒット通知は実行しない。有限の巨大係数1e308を持つ0ヒット5ケースを含む。正本ではダメージ計算のループに入らないため、GPUだけで余分な算術のoverflowを起こしてはいけない。

max_hp_additive/replacementをprivate pending2へ接続した。共有のHP基準計算・software binary64・部位receipt・scalar damageを再利用し、HP×割合→100で除算→flatへ加算／baseを置換する順は保持した。従来のpending1は正本がHP換算を使わないreference_model_gapのため引き続き拒否する。

HP基準の照会には親攻撃の不変な除外maskも渡す。後に書かれた同一burst_castのHPバフは親のHP換算へ含めず、resident buff自体を消さない。入れ子のHP由来攻撃力照会は従来の既定scopeを保つ。正本の実行済みadapterであるapp/damage_query_runtime.pyも参照し、未加工のupstreamだけからscopeを判断しない。hit_countの子が最大HPを増やしても、親3ヒットは最初のHP値で計算する。

追加19契約は両HP方式それぞれの3ヒット、参照固定、0、負、後続HPバフ、現在1024、子HPバフ、部位2箇所、0ヒット部位と、通常基準の巨大係数0ヒット。正本の実際のget_buffs/ref_count/effective_max_hpの戻り値をprofileで記録し、追加照会なし・観測なしとの全battle/trace/RNG保持を確認する。部位では各5670（加算）／709（置換）を含む全会計、親のmain skill列を既存decodeで比較する。

専用診断入口は既存の排他bankへ12word×128件を記録する。kind1=辞書のATK flat/pct、2=現在参照数とpresence、3=最大HP。もう一度照会せず、呼び出し元が得た値を記録する。辞書cacheを使わない入力でも初期化する。通常19と診断19はbank領域外の全59,456,320byteが同一で、41件の順序・binary64値・時刻が正本と完全一致した。

固定通常package `fd83cf9b0e3f76cdd1573a0f9b695f1ab38456e39509b2035001d58f5807e7bb` のMetal291（native218／拒否73）、診断package `c817519be8666ae3585bb6eb830cdc799273915c1418d916558f1cee345a8d08` の19、両方のGPU禁止独立sealが成功した。旧272 input/native指紋と全855,638,016byteが同一、Runtime全field/stride138952も同一。通常19の短いgoldenは通常291の独立sealから該当部分を抽出し、入力SHAを診断19と照合した。

最初の通常291では後続HPバフの2件が不一致だった。最初の診断にはarray sliceをlistと比較するhost不備と、数値辞書cache無効時の初期化漏れもあった。型修正は保存rawのCLI replayで試しGPU追加0、厳密ヘッダー検査によって未初期化を検出した。緩い比較や期待値更新で通していない。HP scopeと初期化を修正した別packageで検証し、失敗capture/raw/claim/replayを保持した。通常291の入力・正本期待値は全て同一、rawが変わったのは276/285だけで、他289入力の909,115,392byteは同一。正本・数値primitive・normalizerは変更していない。

修正版のCPU27群190検査、skip0、66.850秒、正本事前18.697秒、M5 GPU4.416秒、library1.428秒、pipeline8.386秒。診断CPU3群15検査8.423秒、正本1.487秒、GPU0.053秒。分類追記後の対象19検査も成功した。通常・診断のCUDA/MSL事前生成は計4 compiler呼出で、実runは生成cache必須hit・Slang追加0。現CUDAは実行していない。過去・失敗rawのゼロ領域をsparse化して2,820,276,224byteの割当を回収し、全byte/SHA/inodeと14GiBの余裕を保持した。raw削除0。

未対応分類には実証済みの追加範囲を追記したが、全体のgpu_supported等はfalseのままとする。静的入力生成240/266（base180/203）、残35分類、旧266記録と240入力SHAはすべて同一。入力生成と実戦での対応は区別する。

CLI suiteは `full-burst-query`（19）、`full-burst-query-retention`（291）、`full-burst-query-diagnostic`（19）。固定packageの展開先をcwdにしてgeneration、run、sealを実行する。厳密source deltaは初回queryの逆投影と、その失敗packageを基準とするHPscope/初期化修正の逆投影を別々に保持している。

次は未対応35分類の実consumerを優先し、projectile_dmg_pct等の未確認項目を調べる。低bit周期snapshot移動、zero係数・random対象の混在、広いworld/全定義実編成、現CUDAも残る。全キャラ認証0、UI CPU、development_only、最終目標未達。Windows追加操作0、7プロセス終了の原因unknown・環境保全falseを維持する。

記録はresearch/portable-full-burst-query-checkpoint.jsonとresearch/full-burst-query-evidence/。正常・失敗・保存再照合・生成・raw・固定package・claimは各/tmp/nikke-full-burst-query-*へ保持する。
