# 共通の円弧wrap・shift・区間長

`coordinate-arc-scalar`は、着弾確率へ進むための角度演算を共通Slangへ実装する。`coordinate_arc_scalar.slang`はsoftware binary64の剰余・円弧wrap・shift・measureを実行し、既存の`coordinate_arc_sets.slang`を通じて生成区間を差集合／交差へ渡す。CPUは著者定義の入力だけをpackし、出力区間・長さ・ダメージ・確率を先に計算してGPUへ渡さない。

## 数値規約

正の有限periodに対する剰余は、binary64の整数significandと指数を使った除算の余りから求める。負入力は正periodを加えるCPythonの補正を同じbinary64加算で行う。極小の負数では補正結果がperiod自体に丸まる。0へclampしない。probeはperiodを正本と同じ2πへ固定し、入力は有限値に限る。

`_arc`のlength<=0、2π−1e-12以上の全周判定、境界加算、wrap後の出力順も保持する。start=-1e-300／length=1e-300は(2π,2π)という幅0の区間を返す。この区間を削除しない。生成した(1,1)を(0,2)から引くと、正本どおり(0,1),(1,2)の2区間となり、交差は空になる。

measureは既存`event_runtime.slang`の`Sum`／`addSum`をそのまま呼び、有限の補償項を最後に加える。補償式を複製せず、既存実行器も変更しない。probeだけが旧entry名をrenameして既存runtimeをincludeし、未使用の戦闘を呼び出さない。入力・出力区間は有限なので、長さの集計がoverflowする契約は扱わない。

入力2056wordは最大512区間、出力4104wordは最大1024区間とscalarを持つ。非有限、逆転、範囲外、未使用入力の非zero、上限超過はstatus64。幅0と隣接区間は入力で保持する。以前のnondegenerate区間probe135入力の受付・容量は変更しない。本体127対象などの全geometry容量を認証したものではない。

wireのoperationは1=剰余、2=生成、3=measure、4=shift、8=生成被覆の差、9=生成被覆の交差。最初の拡張で旧負例opcode5を有効にしてしまい、GPU検査が拒否契約違反を検出した。失敗を保持し、5を予約のまま残す8／9へ修正した。CPU検査でも正例opと拒否opの重複を拒否する。

## 実証

初期600入力（native592／拒否8）がApple M5 Metal一致・独立seal。生成被覆を追加した640版はopcode負例1件だけ失敗し、修正版640入力（native632／拒否8）が全word一致・独立sealした。旧600の全input／native entryと9,849,600byteのraw出力は名前で対応付けて完全保持した。新sourceの生成CUDA／Metalコードは変更されており、生成byte不変とは主張しない。strict normalizerも変更していない。

正例には±0、極小subnormal、最大有限値、全周閾値の1ULP内外、補償が必要な加算、最大入力、生成→集合演算を含む。scalar・interval順・幅0・未使用tailまで全word比較する。7 CPU検査はpacking中のnative禁止、正本との丸め差、Sum再利用、opcode契約、保存結果の改変も検査する。

最適化までのkernel実行は4回（成功3／比較失敗1）、同じconsumed claimの再試行0。別captureは容量guardでclaim前に停止し、過去の終了raw2件を4KiB単位で疎化して合計2,212,257,792byteを回収した。元rawの4,536,139,776byteと4,419,747,840byte・各SHA・inodeは保持し、raw削除0。入力数・予備領域・上限を減らしていない。

## 共通数値方針の選択

ユーザーは「決定的な共通規約：CUDA／Metalで同じ結果を基準にする」を明示選択した。`coordinate-common-numeric-decision.json`に選択を保存し、監査を`gpu_numeric_implementation_gap`へ進めた。古いMac／Windows sin45の1ULP差と命中反転の証拠はそのまま保持する。

選択と実装完了は別。新しい共通profileのcontract ID・三角関数・精度契約・CPU参照への適用は未完了。公開GPU受付も閉じたまま。既存CPU正本を選択だけで書き換えていない。`model-check`はscalarの証明がpackage内に存在するか、current sourceに一致するかを別々に報告する。別suiteで省略されたproofを成功とみなさず、source更新中のstale proofも表示して開発検証を続けられる。

## 利用と次の接続

```sh
python scripts/nikke_gpu.py package --suite coordinate-arc-scalar --compact --out /tmp/new-arc-scalar.zip
```

新規展開先をcwdにして既存のCPU／smoke／bounded run／sealを使う。standalone probeではresident専用のgeneration cacheを指定しない。Windowsの計算実証は今回実行していない。CUDA／Metalは同じSlang・入力・比較器を使い、現時点の実証はMetalのみ。

次は選択した共通数値規約でacos／atan2／sin／cosと範囲縮約を実装し、円・矩形の幾何arc生成、半径方向の積分、物理packet展開、本体の共通resident実行器へ接続する。全キャラ対応・手動aim・元定義の混合world・公開受付は未完了。詳細指紋と検証記録は`research/portable-coordinate-arc-scalar-checkpoint-v2.json`と`research/coordinate-arc-scalar-evidence-v1/`。

## 配列コピーの除去

生成Metalコードでshiftの各反復に1024区間の配列コピーが3回あることを確認した。最大2つの生成fragmentをstable辞書順で既存集合へ挿入し、触れる区間を同じ規約で結合する方式へ変更した。移動するのはactiveなprefixだけ。出力容量、overflow拒否、幅0、順序、末尾zeroを保持する。

同じ640入力の全10,506,240byteが最適化前と完全一致し、独立sealした。記録したGPU時間は2.516373秒→0.036585秒（約68.8倍）。これはこのprobeの単一測定対であり、全戦闘やCLI全体の速度比ではない。shared_gpu_executeの全体は19.631秒→17.475秒で、Swift起動等の費用が引き続き残る。CUDA／Metalは同じ最適化を使うが、CUDAの実測は未実施。

最適化前のcheckpoint-v1、proof、golden、失敗は保存する。最終CPU18・制御416（Windows専用1skip）と固定full／compactの保持検査はcheckpoint-v2へ記録する。
