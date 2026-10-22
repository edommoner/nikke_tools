# スキルの最大HP換算: CPU契約

`reference --suite skill-hp-basis --out <新規JSON>`を共通CLIへ追加しました。現在は正本CPUの契約段階で、GPUへの接続・認定はまだありません。共有済みの`app/damage_basis_specs.py`を今後のdescriptor定義にも再利用します。

最大HPの加算は、`最大HP × 割合 ÷ 100`を既存のflat ATKへ先に加えます。置換は同じ値をbase ATKにし、ATK%とflat ATKを0にします。加算の位置と乗除算の順序はbinary64の丸めに影響するため、結果4と2になる独立ケースを固定しました。現在HPとの混同、別casterのHP flat、snapshot/copy、期限終了、連続ヒット、部位、吸血、子スキルによるHP変更後も保持する親のsnapshotを含みます。

28ケースのうち26件が正例、2件は保留バーストの参照モデル欠落です。pinned `_fire_pending_burst_dmg`は最大HP換算のmetadataを使わず通常ATKの2250を返し、最大HPの照会もありません。この組み合わせをGPU対応済みとして扱わず、接続時には明示的に拒否します。正本・既存CUDAを合わせ直す変更はしていません。

観測器は実際の`effective_max_hp`の戻り値をprofileし、追加の状態照会をしません。既存の全nativeフィールドとtraceを保持し、profile hookの合成と失敗時の復元を検査しています。結果・packet・最大HP・owner・時刻・照会数・吸血後HPへの故障注入を含む6検査が成功しました。packing/build/executeは禁止したCPU検証です。

途中のfixture想定ではbattle_startの編成順を誤り、owner0の攻撃より後のowner4の付与を先に利用していました。該当するcaster HPとATK相殺のケースを、付与後の周期発動へ修正しました。初回失敗記録は保存し、正本の処理順は変更していません。

記録は`research/portable-skill-hp-basis-reference-checkpoint.json`。GPU sourceは変更していないため、既存Metal971入力の証拠は従来のsourceを指したままです。Windowsの新規検証は0、7プロセス終了の原因unknown・環境保全falseを維持します。次は通常スキルの共通Slang samplerへ接続し、別packageのMetal検証・独立sealを行います。
