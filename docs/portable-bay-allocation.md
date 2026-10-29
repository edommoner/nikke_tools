# ベイの偏差分配：公開比率と未確定の境界

既存のpinned正本は`received_dmg_split`と`self_cover`を規格未定として拒否する。元4段階の効果定義・target・noteは変更していない。今回の調査で公開比率の根拠は追加できたが、incoming実装や受付を解放したものではない。

[GameWithの人数別比率表](https://gamewith.jp/nikke/article/show/444593)は、遮蔽物無しの5人生存でベイ40%・他15%を掲載する。4/3/2人の表示も、重み「本人8・他3」を生存メンバーだけで正規化する候補と表示精度の範囲で一致する。これは表からの推論であり、HP/DEFを変える制御実験やゲーム内部定数を確認した結果ではない。

[Prydwenの著者解説](https://www.prydwen.gg/nikke/characters/bay)も5人の比率を掲載し、Skill2は本人の遮蔽物が対象だと説明する。英語skill本文のall allies記載と解説が区別する誤訳を混ぜない。死亡順や被撃通知をcanonical均等分配と同一とする根拠にはしない。リンク動画は今回視認していない。NIKKE.GGは検索索引だけ・直接取得403、公式技能紹介投稿も取得403として記録する。

## 数値契約へ直ちに昇格しない理由

遮蔽物ありの表には、本人8・他3に対して遮蔽物262という候補が近似的に合う。ただし1人時の表示はcover97.03%・本人2.96%。候補262/(262+8)を百分率の小数2桁へ最近接丸めすると97.04%であり、表示を正確なdouble仕様とは扱えない。不一致を表の書換えや丸め規約の変更で消さない。

追加で必要なのは、正確なcover重みと演算順、元carrierとcover receiverの結合、防御参照元と保護layer順、各メンバーの被撃通知、cover破壊/復活/再burst、本人死亡、均等分配との重複、favorite各段階の実証。均等版への別名化やno-opで静的失敗を減らさない。次は既存incoming/cover/group executorへ落とす明示契約を整える。

データは `tests/fixtures/bay-published-allocation-v1.json`。候補式・表の不一致・未対応flagの維持を3テストで検査する。GPU/Slang/NVRTC/native battle追加0。再調査は正確な定数・制御実験・layer/通知の新しい根拠が得られた時とし、同じ転載の再検索を重ねない。
