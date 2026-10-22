# 回復分配を共有DFSへ接続する次の契約

plan演算の共通Slangは`gpu/heal_share_plan.slang`。独立Metal probe10入力が成功し、GPU0の独立監査でsealした。既存本体へはまだincludeせず、heal_splitの受付は開いていない。CPU正本は共通CLI referenceの4 suite、合計43ケース。これは宣言済みモデルの契約で、実ゲームの意味の保証ではない。

## 検証済みplanと未接続部分

各live carrierを一度だけ5bitのmembership maskへ写す。5人分の隣接maskと重みから連結成分を求め、最大512の重みを各10bit、合計50bitへ格納する。倍率の値や同じcarrierのstack数を重みに使わず、異なるcarrierの重複は残す。孤立した元対象は重み1へ戻す。単独対象はamountを直接渡し、複数対象だけ`(amount * weight) / total`を共通binary64で実行する。0.1の再結合差分、512境界、mask範囲、入れ子planと外側valueの独立性はprobeで確認済み。

probeはliteral maskを入力する演算検査である。実際のcarrierからmaskを作る処理、HP/storage更新、同期子イベント、通知、実編成の対応はまだ証明していない。字句上の小ささや50bit表現からCUDA compilerメモリ改善は主張しない。

## 次の実装境界

1. **membershipの採取。** canonical `_by_stat`はactive順、`_live`は期限→必要時lazy resolve→対象→runtime条件の順。GPUもactivation順のdistinct carrierごとに、squad順で生存対象のlive条件を一度ずつ読む。既存`queryRecipient`はdamage除外やquery-cache条件を持つため、同じ意味と確認せず転用しない。採取後にHPを変えない。
2. **入れ子snapshot。** 現行Frameのvalueへ50bit weights、healthValueへ元amount、既存repeatLeft/repeatPassiveへtotal/member数、cursorへ次の対象を保持する案を使う。元recipient／heal_source／時刻・target・critical文脈も保持する。新mode番号は既存の使用範囲と全codecを確認して確定する。Frame配列を増やす案、深さ別Runtime side tableのどちらが有利かは未測定で、必須とは扱わない。
3. **deliveryと子イベント。** 各対象のbody/storage heal後に既存syncHealthActorを呼び、HP crossingの全子イベントが終わってから次のportionへ進む。入れ子healやnamed removalで外側planを再計算しない。全portion完了後に元recipientへheal_receivedを一度だけ通知する。分配対象ごとの追加heal_receivedは発火しない。
4. **発火元を共通化。** 通常healとlifestealのamount計算順・元recipientの倍率を維持し、amount>0のときだけmembershipを採取する。lifesteal rate<=0は通知しない。rate>0でoutgoing倍率が0ならbody heal0と元通知は行い、planは採取しない。他ownerが吸収率を付与してもheal_sourceは実attacker。修復・蘇生・最大HPgrant・負のamountはshare対象に広げない。
5. **旧経路保持。** 共有statがない入力は既存fast pathを保ち、不要なFrame／work計数の変化を避ける。新しいhealing ledgerの意味を発明せず、既存fieldとCPU側のaccountingを確認する。新statはcanonical identity75を再利用し、64 numeric vectorへindexしない。raw admission／host validator／lazy membershipを一緒に接続する。

## 接続後の検証と停止条件

共通fixtureで43 CPU契約と全戦闘・通知順をMetalへ接続し、元全796のinput/native/raw保持、lazy bank、独立sealを再利用する。相違が出た場合は原失敗を保持し、正本・literal契約・GPU処理のどこに問題があるか確認してから修正する。比較範囲・許容差を緩めない。実編成も全定義を使用し、静的packing増加を全キャラ認定にしない。

Windowsの現行本体assemblyは未成立。新機能のprobe成功だけでCUDA本体の成功を扱わない。追加Windows実行は保存PTXのCPU分析と、原因を判別できる明示compile実験の準備後に限定する。同条件再試行・上限拡大・別level/RDCへの自動fallbackはしない。
