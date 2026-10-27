# 元profileを選択して共通実行器へ渡す

`original-catalogue` は元266profile × 発射体/HPシールド × 3/30秒の1,064名を列挙する開発入口。`cases` はmetadataだけを読み、全profileのprepare/compile/battleを実行しない。明示した1〜4件だけを準備し、元効果/owner順/実武器/育成/configを保持したまま既存の共通typed owner compilerへ渡す。別の計算器やキャラ固有handlerは追加していない。

```sh
python scripts/nikke_gpu.py cases --suite original-catalogue --match 모더니아
python scripts/nikke_gpu.py package --suite original-catalogue --develop \
  --case 'original-catalogue/hp-shield/모더니아/favorite-0/3s' --out NEW.zip
```

未知名・重複・空選択・上限超過はprepare前に拒否する。失敗profileの消去やexpected rejectionへの変換はしない。選択順はcatalogue順へ正規化し、返された行とnative domain、全wire/packed bytesを照合する。未選択profileは準備しない。固定したcase群も同じadapter/selection protocolを使い、callerの`--case`で上書きできない。任意選択は開発専用であり、sealed suiteの基準を迂回しない。

## 初回4入力の結果と次の優先項目

`original-catalogue-initial` はAlice projectile30秒、Modernia shield3/30秒、Privaty Unkind Maid shield30秒の固定群。まだ開発専用で、sealされていない。元266profileの全recordは前回inventoryと完全一致し、静的変換254/失敗12/分類13も不変。静的受理数はGPU対応数ではない。

固定94eb6df1/package3591b6f8…で129unitと全4nativeのCPU gateが成功（77.39秒）。M5 Metalは1回実行し、3件は全比較一致したがModernia30秒はstatus8で停止したため、全体の計算成功/独立認定はFalse。失敗readback/claimは保持し、同claimの再実行はしない。GPU2.370秒、必須pipeline hit0.00297秒、paired generation hit/Slang0。生成CUDA/MSLは旧shield suiteと原byteも同一。CUDAの新実機検証/実CUBIN hitは未確認、Windows新依頼0。

Moderniaの元weapon_changeは通常攻撃扱いのMGであり、`weapon_mode_skill=True`を必須にした最初のwitnessは誤りだった。CPU正本の実射撃は4.0167秒に係数7.71→2.24、19.0167秒に7.71へ復帰する。元定義のskill levelから係数/分類を導き、変更前・変更中・復帰後を全て要求する検査へ修正した。CPU正本や武器/効果の値は変更していない。

実際の未対応は共通`logWorldSkill`の128×48word履歴bank。GPUは129件目で停止し、同じ30秒nativeは1,618件を生成する。新しいcatalogue native検査はこの実件数超過をpackage/runのCPU gateで拒否するため、同じ容量不足でGPUを消費しない。0/127/128受理、129/2048拒否・入力履歴不変を含む15unit成功。共通CLIの既存controller49検査も成功。これは容量対応そのものではなく、未対応を実行前に検出する変更である。

次は**全1,618件の履歴を保持・照合できる共通bank/記録器/decoder**への拡張を優先する。秒数短縮、traceMode抑制、先頭128件だけの照合では解消しない。既存のphysical全件SHA/保持prefix方式を再利用できるか検討し、全rowのsemantic schemaと順序を明示する。旧出力・reserved領域とstrict source ledgerを保持し、新sourceは別packageでMetalを実証してからsealする。現在のguardを成功扱いへ変換しない。

証跡は `research/target-count-query-evidence/original-catalogue-development-v1.json`。BODY所有1typed対象の宣言worldであり、実ゲーム距離規則、任意mixed world、全条件/全キャラ/公開GPU受付の認定ではない。
