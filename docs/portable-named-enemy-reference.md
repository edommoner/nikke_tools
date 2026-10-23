> 追記：共有GPU接続とMetalの限定検証は完了した。最新結果は[名前付き敵GPU](portable-named-enemy-gpu.md)。以下は接続前の正本契約記録。

# 名前付き効果を持つ敵の対象指定

共通CLI `reference --suite named-enemy --out <new.json>` に23の正本契約を追加した。対象は `enemies_with_buff:<名前>` の効果付与、追加ダメージ、名前付き効果の持続時間延長である。GPUの受付・実行器はまだ変更していない。

正本 `BossScript._ranked` はボスを先頭、続いて生存addを誕生順に調べ、`BuffManager.enemy_has_state` でその敵の名前付き効果所持を判定する。付与元casterでは絞らず、同名の効果が別casterから付いていても所持とする。該当なしは空集合ではなくボス1体へ戻る。生存addがいない場合はBuffManager側のセンチネル経路となり、フィルタ呼び出しを行わずボスを返す。これはpinned正本のフォールバック契約である。

効果/instantのrecipient解決は `resolve_enemies`、ダメージの着弾先解決は `route` から同じ `_ranked` を呼ぶ。23契約はbuff/bonus damage/duration extensionの各4通り（未所持/ボス/add/全敵）に、コロン・空白・空文字の名前、期限切れ、遅れて出るwave、退場、同じidの再登場、別casterの印、同名印のunion、明示解除、addなし、ボスを含む128敵を加えた。実際のrank64回、recipient解決57回、所持判定628回を検証した。

名前は最初のコロンより後をそのまま使う。空文字の印も正本では一致するため、GPUの未使用name sentinelと混同してはならない。該当する敵の順序と人数、全候補の実判定、退場後の印の消失をliteral期待値で固定した。同じadd idが再登場しても旧印を引き継がず、未所持ならボスへ戻る。

観測器は実 `_ranked`・`_resolve_enemies` と既存has_state callbackを1回ずつ呼び、追加の所持/数値照会を行わない。23ケースで全battle/skill trace/random最終状態と、get_buffs/所持判定/_by_name/順位/解決/sampleの呼び出し回数を既存の全native観測器と照合した。名前・順序・所属・付与元扱い・フォールバック・期限・回数等の故障を拒否する。

既存 `world_actor_state_native.before_finish` はportableのenemy planがない効果を味方として整形していたため、新しい対象で `ValueError: '__enemy__' is not in list` となった。名前付き敵prefixの観測分類をnativeのconsumerに合わせた。GPU受付の追加ではなく、戦闘・正本・効果定義・通常UIを変更しない。旧175入力の全input/native goldenが同一であることも確認した。

固定package `57a6e33b26608f6deb12bfbe528dbeeb109cd59cca5f51eab7c3413b773b7a0f` でreference23とCPU6群49検査（skip0）、既存175入力のnative事前照合が成功した。前回のGPU source/input/native175を完全保持するため、GPU再実行は0。Slang・NVRTC・driver・Windowsの追加実行も0である。現在の生成cache境界も変更していない。

静的全266profileの記録、237入力SHA、29拒否の記録、41分類のcode/順位を全保持した。4分類だけを `reference_review` から `native_contract_extension` へ移し、未対応の原因から記録済み23契約と次の共有loweringへ案内できるようにした。laneの変更を新しいGPU対応・全キャラ認定へ加算しない。

次は共通の名前operandと敵routeを設計し、既存の敵集合/所持状態/世代管理へ接続する。sequentialの名前付きhit数、stack scaling、発動budget、passive・部位/interrupt文脈、原実編成は追加契約が必要。Metalで新契約と旧出力保持を検証してから受付範囲を記録する。現CUDA/全カタログ・全キャラ対応は未完了で、通常UI CPU・全キャラ認定0を維持する。根拠は `research/portable-named-enemy-reference-checkpoint.json`。
