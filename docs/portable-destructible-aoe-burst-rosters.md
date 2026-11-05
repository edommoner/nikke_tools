# 元AoEバースト・専用倍率とHP/hit盾の共通実行

共通CLIのsealed suite `destructible-aoe-burst-rosters` は18入力（native16・拒否2）。元ノワールのAoE burst、元ミサトの味方盾150%、元トリナのAoE専用435.6%を、既存の同じSlang skill Frame・対象選択・factor sampler・整数damage・着弾receiptへ接続した実編成証拠です。今回、GPUへキャラ別の式や時計を追加していません。

```sh
python scripts/nikke_gpu.py package --suite destructible-aoe-burst-rosters --compact --out NEW_PACKAGE.zip
```

通常のunpack/CPU preflight/required generation cache/run/audit/sealは `gpu-development-cli.md` に従います。新suiteも依存別軽量パッケージを使用し、共通CPUテスト・公開fixture・全GPU sourceを保持します。

## 定義とnative契約

| 編成 | 全prepared定義 | 各本人の元skill定義 |
|---|---:|---|
| ノワール・ミランダ・ドラー・レイ・ミサト | 78 | 8・5・8・7・5 |
| ノワール・ミランダ・トリナ・レイ・ミサト | 83 | 8・5・13・7・5 |

愛用品stage0を正本の選択のまま使い、装備を含む全prepared定義・順序を保ちます。両編成を3/30秒で実行。初期編成はHP・hit・hit破壊後HP・HP破壊後hit・破壊後body・owner世代違いの6条件、トリナ編成はHP/hitの2条件です。盾窓は実BossScriptの2.8→3.2秒で、別CPUイベント列をGPUへ渡しません。

ノワール`피날레`は元の `burst_damage` / `all_enemies`。元route2/count128を保持し、一つのboss bodyに解決したうえで生きた盾を選びます。burst+AoE=true/single=falseで、ドラーのburst+singleと区別。AoEのみでburstなし・AoEとsingleの同時指定はGPUで拒否します。全12正例のAoEフラグをnativeと照合しています。

ミサト150%の時、HP盾へのAoE damageは1,862,720、hit盾では745,088。トリナの元AoE435.6%と普通のatk damage20.9%も作用すると、HP盾5,005,368/hit盾3,942,657です。factor5の順序付きbinary64結果はHP `7.0649999999999995` / hit `5.5649999999999995`。盾150%はHP量だけに加え、hit盾はAoEや散弾の各packetごとにcredit1を消費します。slot順・破壊後の再選択・body復帰・世代違い・全battle/武器/HP/弾薬/gauge/traceも同じ比較器で照合します。

## 証拠と検査

軽量development固定版でMetal14が成功後、専用倍率4入力を追加したMetal18が全件一致し、別processの独立sealも成功。旧14の全input/native/raw 58,720,256 byteをcommon `readback-retain` で保持しました。18のrawは75,497,472 byte、M5 GPU9.758218秒、cached pipeline0.002491秒。最初の14はGPU3.941302秒/pipeline0.007605秒でした。どちらもrequired generation cache hit、追加Slang0、claim再試行0。新しい入力を加えた2回のdispatchで、同一claimの再実行ではありません。

元レイと今回のAoEで比較器を共通モジュールへ抽出。既存の旧141 native/inputと実skill保存5block/61破損検出も同じCPU群で維持しています。新しくトリナHP/hitの実raw2blockをlosslessなnonzero-pair fixtureへ保存し、HP query・damage・skill種別・route・AoE flags・count・receiptの16破損を検査します。fixture再構築の全SHAも照合します。

初回の全定義テストは、stage0のミランダへ愛用品専用定義も要求して停止しました。正本のstage0選択へテストを合わせ、入力/定義は変更していません。保存raw破損テスト追加後のCPU90秒timeoutも原記録を保持。同一入力のCPU戦闘を各変異ごとに再計算する無駄を除き、独立native結果のコピーへ全16変異を照合します。ケース・比較項目・90秒上限は維持しています。最終固定版はCPU47検査を64.962秒、native16の事前照合を10.098秒で成功。共通制御372検査も371成功・Windows専用1skipです。時間上限は90秒のままです。各SHAは `research/portable-destructible-aoe-burst-checkpoint.json` と `research/destructible-aoe-burst-evidence/` を参照してください。

GPU source157・両生成の厳密指紋・全Runtime field/stride138952・binary64/量core・保護CPU4ファイル・pinned upstream・normalizerを維持しました。終了済みrawのゼロ領域だけを疎化して作業容量を確保し、byte/SHA/inode・元の失敗・claimは保持。削除0です。

## 残りの範囲

宣言した単一bossの盾モデルの証拠です。元ゲームの敵盾仕様や全profile/愛用品/geometry/複数enemyを認定するものではありません。分類に今回の限定証拠を追加しますが、packing245/266・base185/203・残20 model gap・全キャラ認定0・通常UI CPUを維持します。旧157だけのAoE正例falseは当時のsuite範囲として保持し、新18の証拠を別項目へ記録します。

Windowsは今回追加実行0。現full battle CUDA実機/compile cache改善の実測は未確認、旧7プロセスの終了原因unknown/環境保全falseも維持。次は貫通、吸血/蓄積・parts/coords/ADDの混在と、必要な短いCUDA確認を優先します。
