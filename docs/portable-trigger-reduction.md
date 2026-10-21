# 発動回数減少の共通実行

`trigger_count_reduce`のbuffを共通Slang実行器へ接続しました。CUDA／Metalは同じ入力・resident walk・整数化・比較器を使います。今回の実機証拠はMetalです。新版CUDA数値一致、通常画面への接続、全キャラ実戦認定は未完了です。

## CPU基準の意味

対象効果と同じcasterの有効なreducerをnativeのresident順で見ます。自身の名前が`target_effect`に一致するか、同じcasterの登録効果にその名前があり、生のtiming文字列が共通なら対象です。解決後に同じ数値になったplaceholder同士を、勝手に同じtimingへまとめません。既存`detail_gpu.compile_effects`が生成するREDUCER_MASKを転置して再利用し、CPUの戦闘状態・カウンター値を入力しません。

加算するのはreducerの`fixed_value`（未指定は0）です。level値・スタック倍率・受益者・現在のruntime条件を加算時のフィルターへしません。発動時の条件検査、失効、削除は既存carrier lifecycleが行います。同名再付与でCPUが保持する最初のeffect定義も、そのまま比較しています。

合計は既存software binary64で加算し、合計後に0方向へ整数化します。元の回数から引いて最小1とします。`.75+.75`は1減少、`-.75-.75`は1増加です。負の減少量で閾値が32bitカウンターの範囲を超えても、64bit整数の閾値として保持して誤って発火させません。入力の固定値はcanonical compilerと同じ±1e8以内、最大512carrierの合計はi64範囲内です。

canonical descriptorのreducible markerと対象eventを使い、通常の`on_attack`、受撃回数、burst回数、burst_enterのstage1には適用しません。`trigger_count_reduce`のinstantにはCPU上で別のstack操作の意味があるため、今回のbuff受付と混同しません。

## 配置と検査

非武器MODEの未使用領域をtagged unionとして使い、固定値と対象256bit maskを置きます。武器変更対象のMODEはそのままです。入力／出力stride・既存の配置は変えていません。専用flag、magic、有限量と上限、maskの範囲とcaster、combat world条件をGPUで検査します。stack metadataの検査もこのtagを共有し、独立したCUDA版のアルゴリズムは作りません。

個別48入力はnative正例40＋raw拒否8です。共有timing、placeholder、caster／recipientの区別、整数化、失効／再付与／削除、各種発射・命中counter、状態免疫metadataとの共存などを含みます。実編成には新たにスノーホワイト：イノセントデイズと紅蓮：ブラックシャドウを全定義のまま追加し、各3秒／30秒を比較しています。

初回287ではフルチャージ2fixtureのGPU時計だけがnative静的正規化と矛盾していました。発射後待機`.1`／最小周期`.1`を、それぞれ`0`／`.2`へ正し、static constructorとの整合テストを追加しました。各入力3wordだけが変わり、native全指紋は不変、GPU計算本体と比較器は変更していません。元失敗・readback・claimは保持しています。

修正版regression287（native232＋拒否55）はMetalで全件一致。旧235と、初回で一致した285の入力・全raw出力・native指紋も同一です。これら2集合は重複するため合算して520入力の認定とは扱いません。成功した固定packageから新golden `research/portable-world-trigger-regression-short-expected.json`を明示sealしました。過去goldenの自動更新はありません。

CPU回帰665件成功（Windows専用1skip）。静的packing189/266、基本キャラ132/203、分類114ですが、全キャラ実戦認定は0です。次の未対応上位には`projectile_dmg_pct`と`trigger_hit_crit`等があります。前者はpinned CPUの計算本体にも処理が見当たらず、単に受け付けるだけの実装では対応済みにしません。数値・対象の意味を定義してから比較可能にする必要があります。

詳細は`research/portable-trigger-reduction-development-checkpoint.json`と同prefixの失敗・時計修正・retention・Metal証拠を参照してください。今回の追加機能についてWindows実行は0で、以前の冷コンパイル失敗と保存PTXの診断結果は保持しています。
