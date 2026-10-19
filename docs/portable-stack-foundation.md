# スタック整数・遅延通知の共通基盤

固定ソース `8516256`。この段階は整数更新と通知保存の基盤です。`buff_stack_add/remove/init`、`debuff_stack_add/remove`、`max_stack_add`、`stack_change_immune` の効果種別を新たに受理する段階ではありません。全キャラ認証は0/203体、通常画面はCPUです。

## 数値規約

CPUの `BuffManager.ref_count` はゲージを整数へ切り捨て、所有スタックの生成・更新も整数を保ちます。小数値のバフ量とスタック数を区別します。参照DoTのbinary64捕捉値は整数値でもsigned31-bitの範囲外になり得るため、今後の操作では既存の捕捉値との整合も必要です。

共通Slangは `int(value or 1)` のゼロ既定値を切り捨て前に適用します。正負ゼロは1、非ゼロの±0.5は0です。removeの符号反転は整数化後です。加算結果は有限上限、次に下限0または1へ収め、最後に整数へ変換します。巨大な有限値でも有限上限へ正しく収めます。無制限指定で結果がsigned31-bitを超える場合はstatus2で失敗し、丸めた成功値を返しません。不正な数値・cap・policyはstatus64です。

`gpu/stack_numeric.slang` はCUDA／Metalで共通です。既存の通常バフ、非参照DoT、対象別発数スタックの増加にも同じchecked incrementを接続しました。Python任意精度整数の期待値19,908件と実GPU結果を比較します。CPUの時系列をGPU入力へ変換しません。

## 更新時の値を保持する通知

複数residentを更新してから子通知を実行する操作では、通知時にresidentを再読すると、その前の子通知による変更を誤って拾います。既存の終了通知と同じ4096件のLIFO予約プールへ、所有者・名前・更新時スタック値を保存します。親の全予約を確保した後で子が追加し、子排出後に親へ戻ります。

既存16bitメタデータ（2件/word）を保持し、並列のuint32値4096件を出力バッファに追加します。GPU私有配列・Runtimeスカラー・Frameフィールドは増やしません。ABIは `0x50455661`、入力77824／出力94208 words、出力は90112から16KiB（約4.5%）増えます。単純な2word/件の配置に比べて小さく、31bitスタック値を損失しません。実使用ピークメモリの測定値ではありません。

9ケースで4096件、4097件目の原子的拒否、不正所有者・値、名前なし、終了／スタック混在、子の再帰排出と値保存、スロット再利用時のゼロクリア、所有者4・INT_MAX通知を検査します。再帰ケースのCPU発動順序と攻撃力2210も照合します。

旧版の全1355入力はABI wordだけを戻すと完全一致し、実GPUの各出力の旧90112 wordsは全バイト一致します。追加末尾はゼロです。物理量・履歴の出力正規化はしません。

## 次の接続で保持するCPU契約

- 味方add/removeは名前完全一致・caster自身を含むresidentのみ、下限1。正のdeltaは上限で変化しなくても有限期限を更新します。DoT時計の期限は更新しません。全residentを変更してから、変化した正deltaの値を元所有者へ通知します。
- initは同名のactive対象が既にあると抑制します。最初の同所有者の登録buffから直接生成し、対象定義の条件・予算を迂回します。通常の名前通知・周期登録・発数寿命の初期化は行いません。
- debuff操作は明示参照の0を保持します。対象の免疫を個別に除外し、一部対象でも共有residentの値を変更します。名前指定の下限0、未指定の下限1です。0でもresident・時計は残り、期限更新・stack通知はありません。未指定はpolarityが厳密にharmfulかつmax_stack>1です。
- max_stack_addはbeneficialで始まる通常buffかつmax_stack!=1へ適用します。共有residentに非対象者が含まれると全体をスキップし、代表と対象別overrideをそれぞれ上限処理します。代表が変化した時だけ期限更新・通知します。
- 免疫はactive対象リスト上の存在判定です。実行時predicate・期限判定・lazy対象の解決へ置き換えません。敵は追加で `enemy_field_visible` による生存・世代一致が必要です。対象操作は現在対象の明示コンテキストを保持し、名前の一致後にも世代を照合します。既存CPUの敵操作ライフサイクル22時点を実行して確認しました（新GPU効果種別の検証ではありません）。
- 操作自体の有限予算は、実際に一致したresidentがなくても通常の対象解決規則で消費します。対象hit counterへの名前付き操作禁止を保持します。
- 通常max_stack=1のrefreshで既存0を1へ戻さないCPU挙動、参照DoT捕捉値、HP再計算と子通知の順序を、効果種別を受理する前に追加照合します。

## 再現

`.venv/bin/python research/verify-stack-foundation.py --backend metal` が新基盤、`research/verify-stack-foundation-existing.py --backend metal` が旧全バイト一致です。同じdriverを `--backend cuda` でWindowsに使用します。全体ゲートは `research/run-stack-foundation-gates.py` です。性能候補は全検証とWindows転送の終了後にだけ評価します。

Macの全22ゲートは成功しました。単体131件、CPU既存25件、58実編成、203武器・203装備・固定8編成、API追加4条件、従来数値34874件・実証4件・状態イベント16件を含みます。58実編成の全項目とCPU参照は前版と一致しました（CPU参照の壁時計測時間だけを除外）。新操作のCPU契約53件も別途成功しています。Mac側だけの証跡は `research/portable-stack-foundation-metal-validation.json` で、CUDA完了の主張は含みません。

Windowsも固定ソース8516256を低優先度・120秒上限の1回、103.038秒で成功しました。本体・数値・通知の入力/出力・source SHAが一致し、本体の正規化生成コード・status・全CPU参照リストも一致します。7分割の圧縮転送を検証し、元HEAD・作業状態・サービスを保持、残存検証プロセス0です。両GPUの証跡は `research/portable-stack-foundation-validation.json`。

全22ゲート・Windows実行・転送終了後、一般のsoftware binary64増加と、同じ検査を持つuint64の+1専用候補を比較しました。1149正例の全出力wordsと数値19908件が完全一致しました。64入力×16384回増加の中央値は有限上限34.327→9.113ms、無制限30.513→9.205ms。実行器の32バフ×64イベント×64入力では53.946→47.470ms（約12.0%短縮）で、各3標本の範囲は重なりません。1回warmup後に順次3回ずつ測定しました。限定負荷であり、実編成全体の速度やピークメモリの測定ではありません。デスクトップGPU活動は除外できません。8516256自体は一般版のままで、候補の採用版は別の固定ソースとして再検証します。

## +1専用処理の採用後（両GPU検証完了）

固定ソース `6e28e63` は上の整数専用候補を既定とし、`PORTABLE_STACK_INCREMENT_GENERAL_CONTROL` で一般版の比較経路を残します。任意deltaの `checkedStackChange` は一般のsoftware binary64処理を保持します。新しい型や効果種別は増やしません。採用版の再現は `research/verify-stack-increment-existing.py --backend metal`、全体ゲートは `research/run-stack-increment-gates.py` です。最適化前 `7d52456` の全1355入力・出力94208 wordsは正規化なしで一致しました。

次の接続のための独立CPU監査では、初期化・max_stack=1の0保持・共有対象の一部だけへのmax_stack_addの11ケースも成功しました。初期化が対象定義の予算/条件を迂回し、発数寿命を初期化しないことを含みます。`research/portable-stack-initialization-contract.json` と敵の世代参照 `research/portable-stack-enemy-contract.json` はGPU受理ケースへ加算しません。

採用版6e28e63も全22ゲートが成功しました。WindowsはBelowNormal・120秒上限で1回、82.486秒で成功し、元HEAD・作業・サービスを保持、残存プロセス0、7分割の保存済み転送も終了しています。最適化前の全1355入力・全出力、両GPUの数値19908・通知9、status・CPU参照・正規化生成コードが一致しました。測定候補と実採用版の生成コードは行指定と空行を除く全行が一致します（コメント追加に伴う空行1つだけの差）。GPU入出力には正規化を使いません。採用の対応は `research/portable-stack-increment-adoption.json`、最終証跡は `research/portable-stack-increment-validation.json` です。

基盤版8516256の証跡はproof commit `7d52456` に保存しています。上記の基盤版と採用版でWindowsの短い検証は各1回、計2回です。効率比較自体はMacだけで、再転送のためのGPU再実行はありません。全キャラ・全効果への接続は未完了です。
