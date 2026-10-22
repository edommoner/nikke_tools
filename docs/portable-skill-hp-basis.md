# スキルの最大HP換算を共通実行器へ接続

`max_hp_additive`／`max_hp_replacement`をCUDA／Metal共通Slangのダメージsamplerへ接続しました。既存の`app/damage_basis_specs.py`を共有し、CPUで戦闘中の最大HPやダメージを事前計算する経路は追加していません。

加算は`最大HP × 割合 ÷ 100`を既存flat ATKへ先に加えます。置換は同じ値をbase ATKにし、ATK%とflat ATKを0にします。演算の順序・加算位置はbinary64の丸めに影響するため、結果4と2になる独立ケースで検査しています。最大HPは既存の`nativeAttackMaxHP`から実行時に取得し、現在HPや表示用同期helperと混同しません。親の連続ヒット・部位packetは生成時の値を保持し、子スキルのHP変更後に取り直しません。

静的descriptorはdamage種別の既存MODE words20..23へmagic・mode・binary64割合を格納します。武器変更・stack・interval・mode entryの領域を分け、未知tag/mode、NaN/Inf、負値、上限超過、別kind、非combatを拒否します。Runtime field追加0、stride138952、CUDA定数48バイトです。binary64・整数変換・pow本体、正本CPU・既存CUDA、strict normalizerは変更していません。元のsource fixtureは置換せず、7既存ファイルと新helperの有限deltaを逆変換し、元のSHA・tokenへ照合します。

`reference --suite skill-hp-basis`はCPU28契約（正例26／モデル欠落2）です。現在HPとの混同、別casterのHP flat、snapshot/copy、期限終了、割合0、連続ヒット、部位、吸血、親子snapshotを含みます。実際の`effective_max_hp`の戻りをprofileし、追加照会をせず、既存の全nativeフィールドとtraceを保持します。

保留B3の2ケースではpinned `_fire_pending_burst_dmg`が最大HP換算metadataを使わず、通常ATKの2250を返していました。この組み合わせはホスト／GPUとも明示拒否し、noopを対応済みと扱いません。GPU37入力はnative26／raw拒否11です。

実編成はメイデン：アイスローズとキロの全定義を保持した3秒／30秒の4入力がMetal一致・独立seal済みです。キロの条件付き保護膜回復はworld経路のkind27／31許可から漏れていたため、既存の共通回復器へ接続しました。別の4入力では、保護膜／デコイの損傷後に回復し、次の攻撃の吸収量が回復なし100から容量基準200／最大HP基準900へ変わることをCPUとMetalで確認しています。`reference --suite skill-hp-basis-protection`でもCPUだけで確認できます。

最大HP半減の2入力は、正本がHP-only付与直後の絶対HPを切り詰めない点で差がありました。既存の静的HP同期ポリシーを負のHP-onlyにも適用し、GPU側の受付も対応しました。正本の境界同期が有効な定義では従来のclampを維持します。通常buff／physicalの演算式は保持しています。

既存8群971入力を元の入力・比較器のまま1回へ統合し、Metal一致・独立seal後、旧全input/native/output entriesとraw3,054,501,888バイトを全byte照合しました。全件同一です。新37＋回復4＋実編成4を加えた計1016入力（native821／拒否195）が同じ115 sourceで確認済みです。回帰CPU340検査成功、full115／commands116の両生成証明書を実証から更新しました。最終sealed packageをfresh展開し、CPU50検査と37入力／native26の事前照合も成功しました（GPU0、claimなし）。

統合CPU検査は最初の60秒枠で330件成功後に停止し、GPU claimなしの失敗を保持しました。統合suiteだけCPU枠90秒とした別packageで340検査が66.540秒で成功しています。GPUの枠は変更していません。最終回帰のGPU時間は10.387秒、生成cache hitで追加Slang起動0です。単発の観測で速度ベンチマークではありません。独立CPU監査は`seal --timeout 90`を使用しました。

初回の比較器で既存healing_storageの復号が不足した失敗は、同source/input/nativeのreplayで保存rawだけを再監査しました。そこで半減HP差を検出し、修正入力を別packageで検証しています。キロ拒否の1入力診断、すべての失敗・claim・rawを保存しています。CPU fixtureのbattle_start編成順の誤認も正本を変えずに修正しています。

メイデンの物理履歴は82／747件で省略0、キロは112／2048件で30秒に32件省略があります。旧レム30秒などの履歴制約も維持します。静的packing222/266・base162/203・73分類はGPU対応率ではありません。Windowsの新規native／compile／GPUは0、7プロセス終了の原因unknown・環境保全false・サービス未識別による停止を維持します。新しいCUDA実行一致は未証明です。通常UIはCPU、全キャラGPU認定0、最終ゴールは未完了です。

証拠・package・seal・失敗・制限は`research/portable-skill-hp-basis-checkpoint.json`に集約しました。次は未対応の`atk_pct`＋`lost_hp_pct`など、正本consumerとHP境界の契約を確認できるものを優先します。未確認のprojectile／shield係数をnoopで受け付けません。
