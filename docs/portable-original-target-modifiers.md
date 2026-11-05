# 元の敵弾・HPシールド補正と共通Frame

`original-modifier-probe` は19入力です。元の完全5人編成・全効果・武器・成長を保持し、2秒ごとの係数100のダメージ定義を1件だけ明示追加します。サクラ／アンカー／エレグ／クレイの敵弾補正、アスカ／レイ／マリ／ミサトのHPシールド補正が、元のtrigger・recipient・期限・条件を経て共通の数値処理に届くことを検査します。CPU算出の射撃予定は入力しません。

この検証で追加する攻撃と対象は、宣言済みV1モデルです。敵弾はkind2、HPシールドはkind3・boss所有世代1・容量1e12。元武器の自動照準・座標衝突・自動シールド迎撃へ接続した証明ではありません。元定義を保持していても、全キャラ対応／ゲーム実機のルール確定とは扱いません。公開UIはCPUのままです。

`portable_target_modifier_input` に、元の補正定義を別axisへ保持するloweringを集約しました。通常の攻撃ダメージ補正へ混入させず、既存共通Slangのcarrier・recipient・factor5・最終丸めを使います。既存のmodifier/shield/roster compilerも同じhelperを使用し、旧入力指紋を固定テストで保持しています。

エレグの元 `target_and_nearby:2` は、BODY1体・部位なし・ADDなし・座標なしの閉じた敵世界を静的検査できた場合だけ、このprivate compiler内でbossへ特殊化します。一般のselector compilerは引き続き拒否し、元の効果定義を変更しません。HP probeでの別のliteral bossダメージ、型違い、所有者・世代違いも拒否します。

アスカの元 `during_shield` 条件は初GPUで受付拒否を発見しました。元条件を除外せず、新しい小さな入口 `destructible_original_modifier_entry.slang` から既存のpredicate受付と `hasProtection` consumerを有効にしました。共通判定の複製・計算式の変更はありません。macro名は既存座標検証由来ですが、この入口は座標コードを有効にしません。

敵弾10入力は各3／12秒、アンカーの別caster負例、レイのシールド補正非混入を含みます。HP側9入力はアスカ／レイ／マリ各3／12秒、ミサト3／30秒、サクラの敵弾補正非混入です。ミサトには元の回復条件を成立させる宣言incoming damageを与え、条件成立前の0と成立後150を区別します。クレイもFB前0／後45.05を検査します。

検証結果と失敗・cache・保持の出所は `research/portable-original-target-modifiers-checkpoint.json` に記録します。CUDA/MSLは同じSlang入口から生成し、同じ入力・native比較器・テストを使います。現CUDA実機の計算・compile cacheの成功は未取得です。分類は `reference_model_gap` を保持し、19packing失敗、座標・selector・全variant・公開統合を未完として残します。

最終19入力はM5 Metal全status0・CPU一致、GPU1.744037秒。別GPU禁止childで全19を3.659128秒で独立監査しsealしました。元敵弾10入力の全input/nativeと約42MBの出力を保持。最終パッケージは関連45／制御480検査成功（Windows専用1skip）、全payload／checkoutと実GPUのsource/input/native/outputを照合しています。監査のhost修正前後もCUDA/MSLと両reflectionは全byte同一、generation cache必須hit・Slang0。新shaderのwarm PSOとCUDA実計算の証明にはしません。

後続の[座標実行器との合成](portable-coordinate-typed-targets.md)で共通typed処理を抽出しました。元の19入力も新ソースでMetal／独立監査を再実行し、保存済み79,691,776byteの全出力を保持しています。追加の座標10入力の実証と自動aimの未対応は分けて扱います。
