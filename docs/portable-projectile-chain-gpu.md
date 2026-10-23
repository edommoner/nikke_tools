# 名前付きスキル終了通知の共通GPU接続

`projectile-chain` のprivate入口は、既存のdamage Frameが全packetとその子通知を終えた後に、同じFrame stackへevent51を積む。CUDAとMetalは同じSlang・入力定義・native比較器を使う。物理射撃からは発行しない。ownerと名前は既存の値を渡し、文字列のコロン・空白を保持する。

buff型 `buff_stack_add` は通常の名前付きcarrierで、instant型の既存stack操作とは異なる。非数値stat92として既存carrier lifecycleへ渡し、敵側でも数値vectorへ加算しない。normal_attackの武器注記はactorの基礎武器と一致する既知種別だけ受け付ける。effectのweapon_typeでactorを上書きしない。

元の係数0では終了通知を発行しない。一方、元の係数が非0で名前倍率により0になった場合は既存の最小damage計算後に通知する。0／負のhit数はpacketを作らず照会と通知を保持する。nativeのゲージ加算は非正値を無視するので、負のhit数をゲージ減算へ変換しない。蓄積放出・親damage固定値・保留B3 bonusの早期returnにはこの通知を追加しない。既存のfull-burst landing Frameにも接続するが、動的参照・混在順序の広い認定は別途必要。

## 実証

Apple M5のMetalで、合成32入力（native24／不正入力拒否8）と、元ラピ：レッドフード全87定義の3秒・30秒2入力がnative一致した。両captureをGPU再実行なしの独立監査でsealした。合成はnested child順、別owner、空名、0／負hit、通常buff carrier、instant操作を含む。全battle・trace・RNGと既存の状態出力を照合し、native observerの詳細handler履歴自体を新GPU専用履歴へ変換したとは主張しない。

合成GPU計算0.044268秒、実編成3.136572秒。初回のパイプライン準備66.165秒に対し、修正版では生成コードを変えず0.002690秒だった。初回のstatus64は旧event descriptorの未使用sentinelを新event51へ残したhost変換が原因で、専用stage0への変換と回帰検査を追加した。失敗capture `/tmp/nikke-chain-metal32-v3` と実行claimは保持する。

Runtime全field・offset・stride138952・CUDA定数48Bは旧Metal460と同一。binary64、strict normalizer、protected CPU/compilerの変更はない。旧244profileの入力SHAは全件同一で、静的packingは245/266、base185/203。追加はラピ：レッドフード。静的packingは全キャラ認定ではない。

旧460込みの492入力（native378／拒否114）もMetal一致し、保存結果の独立sealに成功。旧460の1,447,034,880バイトと新32の100,663,296バイト、入力・native・出力の全指紋が元の証拠と同一。CPU41群281検査（skip0）は95.366秒、GPUは4.549201秒。rawの長さ・全SHA・inodeを保持したままゼロ領域1,106,771,968バイトを疎化し、削除していない。

## 再利用経路と残件

共通CLI `package --suite projectile-chain --develop`、`projectile-chain-rosters`、`projectile-chain-retention` を使う。固定packageをfresh unpackし、CPU gate・generation cache事前検査・Metal実行・保存結果の独立sealの順に確認する。package/capture/指紋は `research/portable-projectile-chain-gpu-checkpoint.json` に記録する。

今回の新full-battle CUDAは未検証。Windowsへの追加実行・観測は行っていない。ユーザーは10月22日の7プロセス終了時にアプリ終了・再接続・再起動等はしておらず、ゲームや動画利用の可能性を報告した。これだけでは終了原因を特定できないため、原因unknown・環境保持falseを維持する。

未対応のall_projectiles、actorと不一致の武器注記、projectile_dmg_pct等は引き続き別のreference／モデル設計が必要。通常UIはCPU、全キャラ認定0、全目標未達。
