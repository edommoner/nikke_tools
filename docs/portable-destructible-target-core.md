# 投射物・シールドの共通状態部品

残20分類は、単なるGPU移植漏れではなく、CPUの対象世界・量のconsumer・attack group producer・仕様自体の不足へ分類した。`consumer-audit` は既存の監査器へ `portable_model_gap_audit` を追加し、pinned4モジュールのAST・未実装表・allied instant filter・nearby fallbackを検査する。consumerや仕様の変更を注入すると監査が停止する。歴史文書は現仕様の証拠であり、全特殊効果という目標から除外する指示ではない。

`destructible_target_state.py` と `gpu/destructible_target_core.slang` は、これらの対象世界を作るための型付き状態処理である。projectile / HP shield / hit shieldは既存ActorKind2/3/4を使う。kind・identityはslot内で固定し、再出現のgenerationは1ずつ進める。期限切れは時刻境界を含み、古い世代や破壊済み対象のreceiptは不達となる。ownerはBODY/ADDの明示handleであり、自動的な親の死亡伝播やshield遮断順を決めない。

入力のdamageとhit creditはすでにcallerが解決した量である。HP型はdamageを、hit型はcreditを残量でclampして消費する。MISS/BLOCKED/DAMAGINGの量の整合性を検査するが、BLOCKEDにhit creditを付与する資格はcallerが決める。倍率・damage丸め・経路・射撃分割はこの部品へ重複実装しない。数値演算は既存のsoftware binary64を共用する。

CPU側は既存ActorRegistryへlive providerをbindできる。失効後のaliveと再出現generationが既存exact/root lookupへ反映される。GPUの14word/slotのarenaはcaller所有で、production Runtime138952Bの配列を増やさない。probeの独立Runtimeは8Bである。部品をbattleの生成・着弾・破壊通知へ接続する作業は残っており、`all_projectiles` や倍率のbattle受付を成功扱いにしていない。

## 検証

共通CLI suiteは `destructible-target-core`。46入力（宣言モデルの正常24 / 拒否22）がApple M5のMetalとCPUで一致し、保存結果を独立sealした。これはpinned native battleの46ケースではなく、新しい状態部品の明示モデルである。生成CUDA/MSLは同じ3ソースから作り、strict normalizationとreflectionを保持する。

正常系はHP / hit量、fractional credit、blocked/miss、expiry、slot127/64の選択mask、同じownerの複数shield、retire/respawn、古い世代・別identity、1e30/2^53の容量を含む。拒否には二重spawn・世代skip・別kindへのslot変更・重複identity・不正owner・非有限値・時刻逆行・不正operandを含む。保存GPU出力5ブロックからID/世代/量/選択を改変する故障検査を追加した。

最終CPUは5群37検査成功、約3.460秒。GPU計算0.002794秒、cached pipeline0.000774秒。旧版との全input/native/output指紋も同一。ActorRegistry接続でCPU reference identityが変わり保存replay guardが停止したため、guardを維持して新固定packageでMetalを確認した。初回と最終のGPU source/input/outputは同一である。途中のpackageからIMPL-STATUSが欠けたCPU失敗も保存し、明示upstream_documentsへ追加した。

## 維持した範囲と次の接続

既存battleの147ソース、全266profile記録、245input SHA、20 issue codeと順位は不変。分類だけを未監査10件からsource gapへ更新し、20 model gaps / review0とした。既存Metal492＋元ラピ2の証拠を保持する。通常UIはCPU、全キャラ認定0、目標未達。

次は共通world scheduleへのspawn/expire binding、明示対象へのreceipt配送、破壊notice continuation、all_projectilesの実選択、projectile/shield倍率の演算位置を接続する。移動・近傍・lock-on・対象数増加・敵弾薬/回復・multi_hit producerも残る。新coreのCUDA実機確認は必要な短い46入力だけで行い、本体の巨大compileや通常battle回帰をWindowsへ依頼しない。
