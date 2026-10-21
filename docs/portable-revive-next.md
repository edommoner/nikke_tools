# 蘇生を共通実行器へ接続する次の範囲

ATK倍率79の次候補として、静的inventoryで複数プロファイルを止めている`revive`を調査しました。まだGPU受付・native同値の認定は行っていません。`projectile_dmg_pct`／`shield_dmg_pct`／`heal_split`はpinned calculator内のconsumerを確認できないため、無効果受付によるpacking件数の増加は行いません。

## 正本の処理

- `calculator/buff_manager.py:3143`以降の`knock_down`は、HP・ゲージ・stack・個人event count・武器変更を初期化します。受けたbuffを除き、`persist_on_revive`と他人へ与えたbuffを保持し、失われた永続buffを記録します。
- `notify_down`は呼出側の後始末が終わってから発火します。同じ通知で復活し得るため、復活した行動を後続のdown処理で再停止しない順序が必要です。
- `revive`はdown集合から除き、HP％遷移を一時的に止め、永続passive／battle_start効果を再付与し、補正後の最大HP×指定％でHPを戻します。永久buffの全再実行ではありません。
- `_reapply_passives`は他の味方に残る同じcarrierへ対象を戻し、stackを二重加算しません。順位で解決済みの対象を戻す処理、倒れたcasterからの再付与、有限bullet効果には別の除外があります。
- `timeline.py:4253`のinstant handlerは生存者をスキップし、復活後に`CharState.on_revive`を呼びます。値0／欠落は正本が例外にします。
- `CharState.on_revive`（2884付近）はcover・reload・charge等の行動状態をresetし、補正後の満弾・next_fire_time=tで再開します。停止中の射撃をまとめて実行しません。

対象selectorも分離が必要です。`allies_down_top_atk_excl:N`と`allies_down_class_random:class:N`は通常の生存者filterを通せません。class_randomは自分を一律除外せず、候補順と正本RNG消費の順序を保ちます。

## 実装と証明の順序

1. GPU・packingを禁止したCPU参照ケースで、戦闘不能→生存のHP／行動／carrier／counter契約を固定する。生存者への蘇生、空集合、passiveの単一／共有carrier、倒れたcaster、HP補正、順位、同フレーム通知再入を含める。
2. 現在のdown処理が失われた永続carrierのidentity・対象別stateを復元可能な形で保持しているか確認する。消去済みなら、容量と再利用世代を明示して既存resident管理へ接続し、単なるbit解除へ縮小しない。
3. 満弾・reload／charge／cover解除・射撃時計と通知の順序を共有Slangで実装する。効果定義・selector・拒否理由を共通化し、Runtime宣言量と生成CUDA規模を測る。
4. 独立fixture→Metal immutable package→実編成→旧集約保持→GPU0 sealの順に進める。既存履歴省略・容量上限・通常UI CPUは明記したままにする。

CUDAのcold compiler allocation failureは別の未解決課題です。蘇生追加を理由に同条件のWindows再試行は行わず、新しいcompiler仮説と成功／停止条件が成立した時だけ短く検証します。
