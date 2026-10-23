# 照準packet観測と対象別倍率

正本の `_fire` / `_charge_fire` の実際のreturn境界を観測し、射撃時に確定したsplit/hit_countと、返却された全HitEventを別々に保存する。返却packet数からペレット数を推定せず、同一damageのassertを緩めて既存結果を通す変更も行わない。既存の単一packet観測器は変更せず、新しい経路を共通CLI reference aimed-packetsへ追加した。

CPU16契約は86射・178返却packet・88private着弾。貫通は6ペレット→12packet、散弾/2銃口は36ペレット→72packet。body/target、aimed、extra、HitEventの全フィールドと順序をSHAで固定した。同フレーム破壊と次フレーム以降のpacket数減少、part対象、RL爆発、吸血も含む。旧24ケースのnative/全trace/private receiptsは完全一致。無観測の正本実行と新観測の全battle/trace/get_buffs/has_live_stat/random.sample回数も一致し、packet順・target・damage・physical split・欠落・HPの故障を拒否する。

共有GPUのsampleDamageFactorsForReachでframe-owned aimの種別を読み、part/interruptのcoreは0にする。直接弾にはpartまたはinterceptの加算項を一度だけ、既存f5へ正本順で加える。貫通/爆発では本体弾と対象弾で倍率が異なるため、ここで一つの倍率へ折り畳まない。既存のbinary64積・round・int/pow・normalizer・Runtime/出力stride/効果定義を変更しない。

Metalの短診断8契約はcore抑止、intercept、part倍率との区別、critical、charge、吸血、part対照。34private着弾を前後状態と順序まで比較する。

次は複数packetのGPU発行。物理射撃数/ペレット通知を保持しながら本体弾→対象弾を既存landing continuationへ渡す。stage本体弾はaddへrouteせず、part/interruptのreach群からaimed対象を除外して二重計上を避ける。前段で捕捉したfactor配列とtarget額を使い、子効果後に再照会・再抽選しない。今回のCPU packet観測がその比較基準となる。area8契約はCPUのみでGPU未対応、development_only維持、全キャラ認定0/UI CPU/全目標未達。

## 実証と保存結果監査

- 現sourceの全1,393入力（旧1,385＋新8、native1,109/拒否284）がMetalで全battle項目/全skill trace一致、独立fresh seal成功。CPU95群498検査175.5653秒、GPU10.5420405秒。新観測/倍率5検査は先行短診断に含み、保存結果ツールの故障検査を加えた最終不変packageもCPU6群28検査に成功した。GPU再試行0。
- 診断8ケースは34private着弾の前後状態と順序も一致し、独立seal成功。normal122source/診断123sourceは完全な包含関係。前回からのGPU変更は `gpu/damage_runtime.slang` だけで、exact ledgerが旧ソースへ可逆に投影する。
- 旧1,385入力とnative指紋は全保持。raw1,361件は全byte一致。残る24件は不要になったcore確率照会のmemo状態72wordだけが変化し、それ以外の旧4,356,832,992byteを保持した。対象はweapon stateのlastSpread/lastProbability/probabilityEvaluationsだけで、計算結果・履歴・RNGの差を除外するnormalizerではない。
- 診断8件は専用bank `[785536,786064)` word以外の25,148,928byteが通常実行と全一致した。入力/出力全hash・review済みsource遷移・native/ケース順・全rawをCPUで照合する `aimed-factor-compare` を共通CLIへ追加。別sourceや古いsource、診断との不一致は読み替えず拒否し、既存出力を上書きしない。
- full package `a6ae7fd8340a154af91fdd173c92814afd273b34b0bed1b72786845b0d233d96`、archive SHA `ca76df45238aa97b70c6828c8ba6c76fce669b2569b48014efdd55009a0404d9`。診断package `085c90937d52ebfde79370f5fcd03c18ee1b18e14c21da39093ccb66ad036c5f`。goldenはそれぞれ `portable-world-aimed-factor-retention-short-expected.json` と `portable-world-aimed-factor-diagnostic-short-expected.json`。

```
python scripts/nikke_gpu.py reference --suite aimed-packets --out /tmp/fresh-reference.json
python scripts/nikke_gpu.py aimed-factor-compare --before OLD1385 --after NEW1393 --diagnostic DIAG8 --out /tmp/fresh-audit.json
```

このcompareは041934bから今回の有限遷移専用で、任意の結果差を受け入れる一般的な許容差ツールではない。全readbackは元path/inode/byte/SHAを保持し、検証済みraw2本から計5,016,911,872byteのゼロ割当だけを回収した。削除0、失敗の再構築やGPU再実行なし。

CUDA/MSLは共通sourceから生成したが、今回Windows操作0で、現sourceのCUDA実行・NVRTC cache hitは未検証。既存7プロセス終了原因unknown/環境保全falseを維持する。現在のMetal実証をCUDA実証へ読み替えない。

貫通の散弾ケースはprivate着弾36件を含み、現診断容量16を超える。次回はケースやペレットを減らさず、排他診断領域への移動などで容量と所有権を明示して拡張する。通常/診断の成功後に大きいfull packageを作り、未接続のarea8を明示したまま進める。詳細は `research/portable-aimed-factors-checkpoint.json` と `research/portable-aimed-factors-evidence.json`。
