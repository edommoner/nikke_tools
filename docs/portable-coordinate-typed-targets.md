# 座標実行器と型付き対象Frameの合成

`coordinate-typed` は、元の完全5人編成・武器・成長・全効果を保持する10入力です。元マルチャーナ3秒の対照に加え、サクラ／アンカー／クレイの敵弾補正、アスカ／レイ／マリ／ミサトのHPシールド補正を座標射撃と同じRuntime内で実行します。クレイは3／12秒、ミサトは3／30秒で条件成立前後も含みます。

型付き対象と2秒ごと・係数100の攻撃1件は明示したV1モデルです。元武器の座標射撃・RNG・通常着弾を保持した状態で、その共通DFSに型付きダメージ・receiptを接続しました。型付き敵弾への自動照準、座標上のHPシールドへの武器迎撃、全キャラ・ゲーム実機のルールを認定するものではありません。エレグのnearby selectorは座標下の参照契約が未完のため、閉じた単一BODY向けの特殊化を流用せず、未対応として残します。

入力は従来の109,968wordの後に型付き5,712wordを追加した115,680word。出力は従来の1,769,856wordを保持し、型付き対象・時計・128件のreceipt・DFS scratchに262,144wordを追加した2,032,000wordです。Runtimeは従来の138,952byteのままで、WorldScheduleとFrame stackを共用します。CPU作成の射撃予定や着弾予定を入力しません。

`destructible_shield_frame_hooks.slang` と `destructible_shield_frame_impl.slang` へ既存処理を抽出し、旧型付き入口と新座標入口から使います。新入口だけが末尾領域へアドレスを切り替え、同じcarrier・対象選択・数値・receipt処理を実行します。座標側の乱数採取では、型付き攻撃も既存のsampled skill frameと同じRNGを使います。MetalとCUDAに別の計算実装はありません。

CPUの元定義・所有者・登録順の一致検査を先に行い、宣言攻撃はその後だけ追加します。通常の座標着弾と、型付き処理によってBODY着弾を抑止した攻撃を別々のreceipt集合へ分けます。後者も時刻・所有者・元source・係数・ダメージ・実対象・完了数を検査し、元の観測traceを保持します。CLIのlive parent再利用時も両方の集合を検査し、欠落・重複・改変を拒否します。独立監査は別のGPU禁止プロセスで全nativeを再計算します。

配置のチェックは既存の共通CLIと監査器を使います。

```sh
python scripts/nikke_gpu.py arena-check --profile coordinate-typed-v1 --out /tmp/new-coordinate-typed-arena.json
```

このコマンドは入力・出力の所有領域とsourceを検査します。計算結果やGPU実行を証明するコマンドではありません。旧sourceの検査には、全file hashと既知差分を固定したinverseを用い、数値normalizerの除外規則は増やしていません。

結果の出所と未完了事項は `research/portable-coordinate-typed-checkpoint.json` を参照してください。公開UIはCPU、全キャラ認定は0のままです。次は型付き対象と座標・自動aimのモデルを結び付け、元の攻撃・武器consumerへ接続する作業です。

M5 Metalは全10status0・CPU一致、GPU2.299065秒／新pipeline92.531390秒。別GPU禁止childで全10を111.541363秒で独立監査しseal。共通化の影響を受けた旧型付き19も別途Metalと独立監査で確認し、保存済み約80MBの出力を全byte保持しました。最終関連53／制御480検査成功（Windows専用1skip）、全input/native/source・各出力SHA、追加のreserved/counterチェックを保存readback全件で確認。完了済みnative監査の再利用は、native関数・producerと入力が同じであることを検査した範囲だけです。GPU計2、計算失敗／retry0。最終generationは必須cache hit・Slang0で、CUDA実機や新PSOのwarm hitの証明にはしません。
