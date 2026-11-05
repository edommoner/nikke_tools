# 座標物理弾の共通数値CPU比較経路

`reference --suite coordinate-physical-common --out UNIQUE.json` を共通CLIへ追加した。
これは選択済みの `coordinate-landing-v1` を実際の `Geometry.landing` 呼出へ接続するCPU比較経路である。
旧CPU正本・上流ファイル・旧passive観測器は変更していない。
ダメージ計算、packet展開、通知、部位破壊、次frameの形状選択は実際の戦闘実装を通る。
本体のGPU接続・公開受付・旧host結果との完全同値を認定するコマンドではない。

## 検査結果

固定full package `437763d5caef8fb22aedf52b25a29aa39678dd2b6ca22372c93a4741c743ee3a`
の9worldで27 logical pellet／47 expanded packetを確認した。重なった部位、割込対象、
2銃口×3散弾、部位破壊後の対象交代、貫通、チャージ、部位命中閾値の攻撃力buffを含む。
共通CLIはGPU build／executeとportable packingを禁止し、全battle・skill traceとsource SHAを保存する。
`stage=cpu-common-policy-contract`、`reference_kind=deterministic-common-cpu`、
`historical_native_equivalence=false` を明記する。

完全遮蔽の初回射撃では共通GL規約のfront確率が1となり、旧host GL規約に残った
0damage本体packetが消える。単なるダメージ差ではなく、body receiptとpart命中閾値が変わる。
旧テストの微小残差と0damage packetは保持した。共通規約でも次frameの積分区切りが変わると
正の残差が残るため、その場合の0damage本体packetは保持する。確率の丸め直しや閾値補正は行わない。

閾値検査は初回6pelletがすべて1000damage、次回6pelletがすべて7000damageとなる。
途中のbuff通知で同じ射撃のダメージを再取得してはいけない。part通知の最終回数は11であり、
微小残差を丸めて12へ変更しない。これは常駐GPU接続で保持すべき実測契約である。

selected CPU36件、control416件（Windows限定1skip）、model-check成功。
compact1643／full2976の全残存record・byte一致、既存GPU source283件と保護7sourceは不変。
GPU実行0、Windows追加依頼0、CUDA cache変更0。既存GPU証拠を新しい戦闘接続の証拠として再利用していない。

初回full packageではmodel-check用の `IMPL-STATUS.md` が欠落した。
失敗packageを保持し、上流文書・arc goldenを明示収録してfrontier検査をCPU必須群へ追加した。
修正版は別package・別captureで検査した。

## 次の接続境界

既存 `WEAPON_TYPED_DAMAGE`／`WEAPON_TYPED_PELLET`／`WEAPON_BODY_AMOUNT` の呼出順を使い、
GPU内で保存した着弾確率からpacketを作り、全pelletの通知後に着弾させる。
`WORLD_TEAM_PELLET` の従来body-only通知をそのまま併用すると二重通知になるため、
part/body/crit/coreのfraction通知とreceiptを一つのprofileで接続する必要がある。
部位名から現在世代への着弾時解決、同射撃内のsnapshot固定、BODY/ADDとPART/INTERRUPTの集計差を保持する。

現在のresident物理GPUはbody-onlyの制限を維持する。新しいCPU経路はprocess-global patchを
scope内で使うため同一processで並列実行しない。expected以外は実行前に拒否し、例外時の復元も検査する。
RNG・手動aim・cache key丸め・全原定義・現在のCUDA実証は引き続き未完了。
証拠は `research/portable-coordinate-physical-common-checkpoint.json` と
`research/coordinate-physical-common-v1-evidence/` に保存した。
