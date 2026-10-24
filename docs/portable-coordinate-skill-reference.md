> 最新追記: referenceは同cast内消滅後packetの契約を加えて25件へ拡張した。正本kind/accountingの説明を訂正した。新GPU部品21入力と最終回帰は[座標GPU部品](portable-coordinate-scene.md)を参照。以下の24件・CPU49件は前段階の記録。

# 座標スキルの正本契約とtyped receipt接続

共通CLI `reference --suite coordinate-skill` に、円／回転矩形・前後順・全部位／距離選択・破壊／不壊を含む24契約を追加した。新規full固定packageでGPU／packing禁止のまま全24が成功した。GPU受付は閉じたままで、座標GPU対応の証明ではない。fixtureは既存のauthored effect／weapon metadataを置換する正本ハーネスを再利用し、実キャラ全効果の認定とは区別する。

```sh
python scripts/nikke_gpu.py reference --suite coordinate-skill --out NEW_NATIVE.json
python scripts/nikke_gpu.py consumer-audit --out NEW_CONSUMER_AUDIT.json
```

## 正本で分かれる選択

|スキル|追加対象|interruptと総量|
|---|---|---|
|通常bonus、markerなし／false|追加なし|本体だけ|
|`hits_parts=true`|現在liveの全部位。距離に関係なく、geometryの前→後の順|interruptを選ばず、部位量をcaster totalへ加算|
|通常貫通／爆発|現在aimの範囲円とshapeが接するlive対象。範囲buffで拡張|部位はtotalへ、interruptは別accountingへ|

`hits_parts=true` では貫通／爆発statでも全部位選択が優先される。非座標のreach経路をそのまま使うとinterruptの扱いを誤る。24ケースはslot0のauthored source、0.25秒、通常／貫通／爆発、marker absent/false/true、範囲0/200%、前後順の逆転、次cast前の部位破壊・不壊を比較する。固定値本体2000／部位3000を基準に、通知とpacketの全順序、名前付きhit数、gauge、interrupt別量を検査する。profile observerは元geometry／selectorの戻り値を読むだけで、追加query・再計算・route上書きは行わない。元観測器との結果・trace一致、既存profileへの連鎖・復元、入力不変も検査した。再利用判定は同一geometry signatureを複数回観測した場合だけ検証する。

## 実行を妨げていたCPU bridge

最初の座標実行は `Unknown world actor (explicit handle required): stop` で停止した。旧typed impact bridgeは `_land_target` の吸血直前で無条件にPART receiptを発行しており、正本が返すinterruptや消滅済み対象の区別を使っていなかった。

`impact_runtime.Landings` が `boss.hit_target` の戻り値を専用localへ捕捉し、元の条件分岐・総量加算の後でPARTの場合だけpublishするようにした。hit_targetは元の1回だけで、戻り値の再計算はない。順序は **native hit_target→元のpart total更新→typed impact→元の吸血** を保つ。private interrupt kind6をcanonical ActorKindへ追加したり、部位へaliasしたりしない。正本hit_targetは消滅済みでもkindを返すため、この条件だけではstale partの通知を抑止しない。前版の「消滅済みではtyped creditを作らない」は誤った説明で、実装の正本accounting保持とは分けて訂正する。reserved localの既存使用やsourceのcapture件数不一致はinstall時に拒否する。

unit故障注入は部位／interrupt／空の戻り値と実行順序・一回呼出しを検査する。座標契約の故障注入で通知順の検査不足も見つけたため、通知数とpacket配列だけでなくliteral event-kind列を追加した。旧正本CPUファイルや計算式は変更していない。

## 未対応分類と数値設計

既存のmodel-gap監査へ `coordinate_world.classification=gpu_port_gap` を追加した。正本consumer `_coord_skill_hits` は存在するため、nativeモデルがないstat群とは別に扱う。全部位選択とshape.contains選択のAST、現在のhost GPU拒否guardを検査し、その変更には新しいport証拠を要求する。`effect_range_pct` 等の既存未実装stat分類は維持する。

数値段階は分けて移植する。全部位指定は選択時の距離積分を使わないが、live世代／depth順とaccountingが必要。通常の範囲skillはShape.dist/containsのhypot・回転のradians/sin/cosが必要。通常弾の期待値分布には、さらにacos/atan2・一般pow・角区間の集合演算と10点Gauss–Legendre積分がある。乱数モードは角度要否によるdraw数も別契約になる。今回の24契約から、これらの物理確率計算やMetal double実装の成立を主張しない。既存software binary64やstrict normalizerは変更0である。

## 回帰と残件

最新のmixed81を使う固定compact packageで、関連検査を加えたCPU49件と既存81入力／native68件が全一致した。入力指紋と旧goldenは不変。共通制御392件（Windows専用1skip）も成功し、full/compactの残存全recordは一致した。GPU source・入力・native指紋が変わらない既存Metal81を再利用し、GPU再実行0。新しいreferenceのGPU支持フラグはfalseを維持する。

次は共通の座標descriptor・部位選択／範囲形状・数値primitiveを接続する。座標のhost guardを先に解除しない。通常UI CPU／全キャラ認定0／静的245/266・base185/203／残20分類は維持する。Windowsは追加依頼0、既存PTXの状態は接続復旧待ちでunknownであり、再実行しない。証拠は `research/coordinate-skill-reference-evidence/` とcheckpointを参照する。
