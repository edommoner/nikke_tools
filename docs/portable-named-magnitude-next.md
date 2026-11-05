現在の実装・Metal588検証は[portable-named-magnitude.md](portable-named-magnitude.md)を参照してください。以下は実装前の参照確認と計画の履歴です。

# 次候補：名前付き効果の倍率変更

これは参照確認と移植計画で、共通GPUへの受付はまだ追加していません。現在の未対応106分類のうち、dmg_scale_mag_pctはブレイディ／イブ、received_dmg_buff_mag_pctはエマ：タクティカル・アップの定義を阻みます。静的packing199/266や全キャラ認定0をこの準備で変更しません。projectile_dmg_pct／shield_dmg_pctはtaxonomyにありますが、この調査では参照側consumerを特定できていないため、無効果として受付へ追加しません。

## 参照契約

- pinned calculator/timeline.py:4875以降のdmg_scale_mag_pctは、通常の係数取得・stack scalingの後で、対象damage効果と同じ名前をtarget_effectに持ち、同じcasterで、時刻がexpires_atより前のactive carrierを順に読みます。係数へ(1+mag/100)を逐次乗算します。このループはrecipient/runtime conditionを独自に再判定しません。汎用queryRecipientへ置き換えると意味が変わる可能性があります。
- 同処理はB3 bonus damageのpending追加より前にあります。保留後に最新倍率を読み直す設計へ変えず、既存pendingの係数保存へ接続します。DoTとstack係数の順序も守る必要があります。
- pinned calculator/buff_manager.py:4678以降のreceived_dmg_buff_mag_pctは、通常のreceived_dmg_pct加算を保持した後に「base_val*(mag/100)」の増分だけを追加します。倍率carrier順→同名base carrier順、各対象・期限・runtime条件・lazy解決と_get_valueのquery actorを保持します。基礎値の合計へまとめて乗算すると浮動小数点の加算順序が変わります。
- 正本NAMED_MAGNITUDEは78／79／80とtarget_effectの名前IDを持ちます。ただしatk_buff_mag_pct（79）の移植も別の参照契約で、78／80へ汎用的にまとめたというだけでは対応済みにできません。新しい巨大Runtime配列は追加せず、既存carrierと名前参照を使う方針です。

## GPU禁止の参照確認

`.venv/bin/python research/verify-portable-named-magnitude-reference.py --out /tmp/new-reference.json`。既存native observeを利用し、portable build／executeとlegacy detail GPU runを禁止します。baseline・received増幅・違う参照名、damage baseline・倍率増加・違うcasterの6ケースが成功しました。記録はportable-named-magnitude-reference.json。

この6件はdamage projectionだけのconsumer確認です。最初の試作では、未対応のenemy magnitude carrierを既存named-state observerがalliedと解釈し、`__enemy__`の名前解決で停止しました。参照計算の差分とは未判定です。現在の準備用probeはnamed-state観測を無効にしており、これをGPU一致検証へ転用してはいけません。本移植ではenemy metadataとobserverの正しい接続を先に用意し、全状態・元の比較器を保持する必要があります。

## 実装と検証の順序

1. 78の係数準備／pending保存と80のenemy modifier後処理の接続箇所を固定する。原正本・protected referenceは変更しない。Python loweringとGPU受付のtarget_effect／kind／stat／private worldの契約を一致させる。
2. 名前違い、caster違い、複数倍率の順序、失効境界、named子、stack、runtime条件、lazy敵対象、敵世代／再出現、pending前後の倍率失効を独立fixtureへ追加し、unsupported observerを直して全状態を比較する。不正name・flag・statのraw負例も作る。
3. literal→実ブレイディ／イブ／エマ編成→集約回帰の順に、新しいimmutable packageでMetal検証する。旧530のinput／全raw／native保持とstrict CUDA/MSL normalizerを確認してからseal。Windows本体はv115 cold失敗が未解決であり、同条件再実行はしない。新たなcompiler仮説と成功基準を先に定める。

受付が参照仕様と一致しない、observerを弱めないと通らない、旧rawが変わる、バースト保留の順序が不明な場合はsealしません。通常UI GPU化・全キャラ認定・CUDA実数値一致は別に未完了です。
