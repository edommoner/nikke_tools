# 実際の共通入口で未対応項目を調べる

開発の優先順位は、使用する入口の`entry-inventory`から決める。従来の`inventory`はlegacy world compilerの分類であり、共通座標入力やtyped modifier loweringの受理範囲とは異なる。いずれも静的変換で、GPU受付・計算・全キャラ認定を表さない。

```sh
python scripts/nikke_gpu.py entry-inventory --suite coordinate-original-owned --out NEW_ORIGINAL.json
python scripts/nikke_gpu.py entry-inventory --suite original-projectile-weapons --out NEW_PROJECTILE.json
python scripts/nikke_gpu.py entry-inventory --suite original-shield-weapons --out NEW_SHIELD.json
```

元のprofile準備、KindAdmission、元source行への逆対応、診断分類、GPU禁止contextを再利用する。後ろ2つは実際の`compile_coordinate_typed`を使い、kind2/3の1対象、明示BODY owner、固定の宣言形状、自動照準/現在敵field policyを記録する。模擬damageを追加せず、元effect/ownerを変更しない。これは既存13/15入力suiteの全ケースを再実行するコマンドではなく、同じcompilerへの全profile静的調査である。

入力変換失敗には、選択した入口と同じ既存group/target-modifier loweringを使う定義単位の診断を添える。エラーのidentity/stat/targetは変換前の元行を保持する。validatorの最初の失敗しか分からない範囲、全programの失敗、definition-kind拒否を分け、後続要件を解決済みと予測しない。未知policy/別sourceの組合せ、壊れたaxis/source対応、battle/GPU呼出し、出力上書きは拒否する。

現在の観測では全266profile中、legacy worldは245、元共通座標は247、宣言した発射体/敵シールド入口は254が変換できる。247からの差はSakura/Anchor/Clay/Asuka/Rei/Mari/Misatoの7profile。元266件の定義identityは同一で、GPU source/計算実装の追加ではない。残る12profileの失敗を13の元stat/target分類で保持する。全キャラ認定0・通常UI CPU・公開GPU受付Falseは変えない。

`multi_hit:2/4`はNihilister/Belortaの元定義のまま共通入力へ下ろせ、実際のgroup owner maskも存在する。既に単体/実射撃/長時間/混成の限定実証があり、同じprobeを作り直す優先度は低い。一方、現在の座標modelで複数の論理敵へ同時に当てる経路や、既定CPUのproducerとは別問題である。PARTをBODY/ADDと同じ敵数へ置き換えたり、単体typed shieldを敵数として数えたりしない。変換成功からthreshold発火を推定しない。

次はこの一覧をruntimeの未実証条件と照合し、受理される元profileの選択・固定・bounded実行をCLIで反復できる経路を優先する。12件のmodel gapは別に残し、既存の実証や単なる変換を全効果対応へ昇格しない。今回の変更は監査/診断/CLI routingだけで、Metal/CUDA計算とWindows実行の追加はない。
