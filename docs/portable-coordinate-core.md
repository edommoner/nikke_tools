# 共通実行器のlive core

private `coordinate-core`を追加し、coreの中心座標・選択・既定照準を既存の物理packet実行器へ接続した。M5 Metal120入力（共通CPU106／拒否14）が全word一致し、保存rawから独立seal。追加28core worldとIR拒否8件を含む。旧84のnative/output指紋を保持し、raw先頭440401920byteも旧保存物と全byte一致した。入力は旧108648wordを保ったまま144wordを追加し108792word、出力1310720word。全キャラ認証0／モデルgap20／公開GPU閉鎖／UI CPU／全体目標未達。

## 状態・数値・定義

coreの開閉・期限・再出現・start時刻は既存world graphが管理する。新IRは32nodeの静的中心座標と、既定照準か明示照準かの区別だけ。選ばれたcore、frame別schedule、確率、ダメージは入力へ入れない。CPU正本の`_apply_geom`と同じく最大径を選び、同径なら新しいstart、その次に後の宣言順を優先する。base coreは原点で、同径のlive nodeが優先される。既定照準は選択core中心、coreがなければ原点。明示照準は維持する。

選択coreを既存CL積分器の128番目のshapeへ渡す。127対象＋coreの容量を保持し、core_open／core_under→条件付き本体core確率→共通damage factors→packet整数丸めをそのまま再利用する。部位に隠れたcoreは通常射撃ではcore_open0、貫通・爆発ではcore_underを使う。core・crit・team通知と残差、full-charge親量も既存処理を使う。CPU正本、binary64／pow／整数変換、通常のCUDA／Metalで別々の効果本体は変更していない。

coreの既定照準はordinary範囲skillの選択にも接続する。部位着弾が別のnative HitEventとなるため、既存`logWorldSkill`で実packetのskill traceを記録する。元の着弾量・queue・通知を再実行する処理ではない。

## 実証

中心core、base core、偏心と明示照準／既定照準、部位遮蔽、貫通、爆発、critとcore倍率、core通知の蓄積・子buff、遅延open、expiry、reopen、最大径、同径でstartと宣言順が競合する場合、baseとの同径・大小、選択core失効後の復帰、大／小core、散弾×2銃口、2射手、owner4、展開親量、32node、127対象、既定core照準の範囲skillを検査した。全106worldは720論理pellet／2037着弾packet。core通知記録720件には0fractionの呼出も含み、720命中という意味ではない。既存のpassive observerがfractional hit／残差／team／全戦闘と順序付きpacket traceを比較する。

初版120は2件失敗した。爆発のfixtureでglobal weapon metadataだけをRLへ変えたため、static combat typeとnativeの発射後待機時間.215が不一致だった。武器種を同じliteral combatへ明示し、待機時間も揃え、以降のmetadata不一致をpacking前に拒否する検査を追加した。もう1件は範囲skillの実ダメージとpacketが一致したが、旧skill traceが部位HitEventを落としていたため、共通loggerへ接続した。正本や期待ダメージを合わせ込んでいない。初版のsource/package/capture/rawと比較診断を保持する。

新GPU2回（初版失敗1／修正版成功1）、同claim再試行0。修正版GPU .246820秒、PSO compile90.560575秒、shared execute95.164267秒。Slangは事前生成cacheを必須hitにし、GPU実行中のSlang呼出0。新しいMetal shaderの初回compileが待ち時間の大半。

## CLI・cache・保存

`package --suite coordinate-core --compact`はsealed120入力を作る。通常の新規展開→CPU preflight→bounded run→保存結果監査を使う。新entry専用の完全stride受付を設け、旧entry／不完全なstrideは拒否する。header・node count・auto flag・reserved・非core座標・非finite core座標・未使用nodeを拒否する。旧scene compilerは既定でcoreを引き続き拒否し、専用adapterだけが明示受付する。

通常81／97は、同じpaired generatorを固定packageで使いCUDA/MSLの全生成byteが過去保存物と同一と確認した。別途旧81／97のGPU再実行0、CUDA compile0、normalizer／cache key変更0。現sourceと違う旧証明書を新proofへ昇格させず、exact inverseで履歴監査する。旧sealed packageは保存時のsourceを所有し、現sourceの新package受付とは区別する。生成byte保持は厳密cacheを再利用できる条件の証拠であり、Windowsの実cache hitや現CUDA計算成功は未取得。

最終immutable packageでCPU59件、control416件（Windows専用1skip）、model-check成功。full3024→compact1715の全残存record／byteが一致し、実証済みGPU source identityも一致。保護7source保持。独立source certificateはsource-onlyであり、CUDA compile/cache/計算proofではない。Windows追加依頼0。

旧raw1件と今回の失敗／成功rawを全byte・SHA・inode保持で疎化し、2294730752byte回収。raw削除0、入力削減0、実行時の1GiB reserve保持。失敗記録も残す。

次優先はGeometryの丸めcache keyと再利用規約。その後manual aim／layer2、sampling RNG、物理group・ADD共有、座標sceneの敵攻撃／buff等の混在、全元定義と公開受付。通常経路の同一生成byteを使った保存結果の厳密な再結合もCLI効率化の候補で、現時点では未実装。集約は`research/portable-coordinate-core-checkpoint.json`、証拠は`research/coordinate-core-v1-evidence/`。
