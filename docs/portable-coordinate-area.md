# 座標形状から実戦着弾への接続

`coordinate-area` は私有の共通世界実行器へ通常の貫通/爆発の距離選択を接続する。M5 Metalの52入力（native42/拒否10）と、同じshape関数を使う小probe158入力（native150/拒否8）が一致し、保存rawの独立sealも成功した。Windowsは入力preflightでhost三角関数差を検出して停止し、GPU実行0。全キャラ認定0、UI CPU、20gapを維持する。

## 共通実装

静的形状の角度は読み込み時に `portable_coordinate_area_specs` が回転行列へlowerする。GPUへ渡すのは静的定義と行列係数であり、距離・選択集合・ダメージ・時間展開をCPUで計算して渡さない。common appコンパイラは正規化済み武器爆発半径を引数に受け、研究用観測器へ依存しない。

`coordinate_shape_math.slang` の同じ整数binary64距離/contains/行列検証を、実戦と小CUDA probeの両方が呼ぶ。円・回転矩形の演算順とtouch=1e-9を保持し、既存 `coordinateHypot` を使う。live frame集合をdepth順に走査し、既存照準snapshotの対象中心またはauto_aimで選択する。範囲はその時刻の共通buff quantityから計算する。hits_partsは引き続き距離に関係なくPARTのみ。

新entryの狭いcompile-time hookで既存world callerへ接続し、既存Slang/正本CPU/binary64/normalizerは変更しない。既存のFrame.interruptAmount/interruptReachと38word receiptを使い、Runtime追加配列0。選択時のkind/slot/generationを既存coordinate packetへ固定し、PARTは既存counter publication、INTERRUPTは別HP/量・吸血へ着弾させる。INTERRUPTをPARTのtyped counterへaliasしない。

## 実証

42正例は既存19、未接続だった通常範囲8、既存DoT9、新6（circle touchの1ULP内外・矩形0/45度・layer2照準中心・範囲buff失効）。全battle・時刻・選択key/世代・量/順序・interrupt accounting・counter/吸血を比較する。shape小probeは150数値/containsを全word比較する。

初回の1差分はlayer2設定をGPU compiler environmentへ渡していなかった入力不備。原本CPUと期待値を変えず、設定を同期し競合指定を拒否して解消した。初回失敗raw/claimは保持。修正版の他51blockは初回と全byte同一で、旧19は全79691776byteとnative recordを保持した。

修正版M5 GPU .021895秒、Slang2.438659秒、cold pipeline7.095402秒。小shape GPU .000118秒。新Metal3回（初回差分、修正版、小probe）、同claim再試行0。別captureの容量guard停止はGPU0。容量を下げたりケースを減らさず、完了済みrawのゼロ領域を疎化して全byte/SHA/inodeを保持し計1731018752byteの割当を回収した。raw削除0。

最終area CPU31/shape CPU6、共通制御394（Windows専用1skip）、追加のinput診断12/モデル分類7が成功。full2893→compact1599の残存全record/サイズ/SHA/byteが一致。5種類の保存raw改変（boundary選択・照準中心・interrupt量・世代・未使用tail）を検出。旧35/24/16/81/hypotのGPU閉包は不変なので再実行していない。

## Windowsで確定した数値方針gap

小shapeだけを固定packageから低優先度2GiB/外180秒・内60秒で1回依頼した。CPU6件は成功したが、static input45行がgoldenと一致せず、native150/GPU/compile前で停止した。再runは依頼せず、prepareだけのCPU診断とliteral境界1件で原因を確定した。失敗・claimは保持。監視process14件欠落の原因はunknownで、保全成功に変更しない。詳細Windows診断は外部公開していない。

同じbinary64のradians(45)に対し、観測したMac Python3.12.15のsinは `0x1.6a09e667f3bccp-1`、Windows Python3.12.14は `0x1.6a09e667f3bcdp-1`。これは入力だけの差に留まらない。中心0/幅2/高さ100/45度の矩形、点(0,16)、grow=`0x1.4a09e6676a4c6p+3` は、Mac原本で命中、Windows原本では非命中になる。

原本を両方保持したまま同じGPU結果を双方へ完全一致させることはできない。ユーザーへ数値基準（既存Windows/決定的共通規約/現在Mac）の選択を依頼中。選定前に誤差許容を加えたり、Windows入力へgoldenを合わせ直したり、CPU原本を変更したりしない。`tests/fixtures/coordinate-native-trig-policy.json` とsource-bound model auditに `reference_numeric_policy_gap` として記録し、公開GPU受付は閉じたまま。

## 入力差分の自動診断

共通CLIは入力gate不一致時、既存の静的bytesから `cpu-input-mismatch.json` を保存する。件数/名前/期待・実SHA/フレーム整合性を最大64行まで記録し、raw入力を含めず、診断自体はnative/GPUを追加実行しない。既存診断ファイルの上書きも拒否する。観測済みWindows inputSHAを完全再現する45箇所の差分で自己検査済み。guardは弱めていない。

## 利用と残件

`python scripts/nikke_gpu.py package --suite coordinate-area --compact --out PACKAGE.zip`。期待値と小さいMetal証拠は `research/portable-coordinate-area-short-expected.json` / `research/coordinate-area-evidence/`。shapeの独立suiteは `coordinate-shape`。

数値基準選定、手動座標aim、座標の通常物理確率/RNG、保留B3モデル、跨frame同名世代交代、summon/迎撃弾などとの混合world、原キャラ全定義と公開受付は残件。今回のdeclared casesを全キャラ対応に数えない。
