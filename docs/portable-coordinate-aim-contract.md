# 手動照準・カメラ調停の共通実行器への接続契約

共通CLI `reference --suite coordinate-aim-common`へ30件の実戦契約を追加した。canonical simulateが実際に行う操作要求、window／anchor照会、調停後のframe照準、物理／範囲スキルの照準照会をpassiveに読む。新しいスケジュールや選択結果をCPUでGPU入力に埋め込む方式ではない。共通数値のlanding／area distanceを用い、元CPUのファイルは変更しない。

30件、1652frame、実際の照準照会206回が検査に成功した。4状態窓（always／burst_charge／burst_chain／own_full_burst）、5アンカー（combat_start／fb_end／own_fb_end／next_fb_start／own_buff_end）、reload_total動的減算、burst使用者gateを含む。最初の生存entry、core消滅・移動、対象の実破壊、優先度先占・同順位の新要求、warn全員操作、レイヤー1／2、共有カメラ、0値focus markerの期限切れ、全バースト追従、強制focus sequenceを扱う。別unitでstrict競合の拒否も検査した。11秒の予測ケースは最初のcycleで閉じ、full burst終了後の実予測clockから開く。

## フレーム内で照準を解決する位置

`timeline.simulate`はbossのframe更新→`bm.tick`とイベント／burst処理→squad sequence→`_arbitrate_control`→`_resolve_aims`→各character tickの順で進む。前半の定時skillは前回の照準を読み、後半の物理射撃は今回の照準を読む。3件の実照会で同時刻の後半frame照準との差を保持した。同順位の新要求が割り込むケースでは、定時skillが旧[0,0]を読み、後半の物理射撃が新[40,0]を使う。全照会を同じframeの新しい点へ揃えてはいけない。

GPU接続では既存のGeometry snapshotと操作調停器を再利用し、5人分の照準点／targetをframe間で保持する。coreが移動したり標的が消えたりしても、前半handlerが旧点を読むので、target slotから現在の中心を毎回引き直す方式では足りない。actorの実破壊もframe内の残り射手の照準を即変更しない。Geometryのcacheは照準移動で破棄せず、既存の(ax,ay,R,grow)キーで共有する。

既存`focus_aim_runtime`はカメラmask・focus marker・全バーストの土台、`world_charge_control_runtime`は要求の優先度と新要求edgeの調停の土台として使う。手動aimの要求は他軸と合流させ、同じ優先度なら元の非aim要求を優先する。shared cameraでは各カメラ担当が自分の手動点を持ち、追従する他射手は先頭カメラの点を使う。全員を単一lead点へ置き換えない。

候補state領域は既存CF_END919840からGeometry cache BASE920000までの160wordの隙間。接続時には新entryのarena監査を通し、既存profileのreserved zeroとsource／生成byteを保持する。現時点ではこの領域への実装・割当は行っていない。

## 静的IRと未接続部分

`portable_coordinate_aim_specs.compile_aim`は元のnative normalizerを再利用し、著者指定target slot／core、entry順、priority、4window／5anchor、offset／lenのbinary64、raw buff名、gate mask、reload_total減算を保持する。default priorityはlive must_breakの所属でMID20／HIGH30が決まるため、-1という明示sentinelのまま残す。利用者がpriority=-1を指定したものとは区別し拒否する。

現在のprivate IRは1人8entry、target slot1..127、priority0..99、有限offset／lenの絶対値180秒まで。coreを予約し同名label／body slot alias／重複slotを拒否する。別のcontrol軸やsquad sequenceの存在も明記し、aimだけを取り出して元のclick／reload等を捨てない。実行側のwindow／anchor／予測clockとcallerは未接続なので、IRを作れた件数をGPU対応数として数えない。

CLI検証はGPU build／execute0、packing0、約3.12秒。結果の詳細8,187,371byteをローカルに保持し、共有用summaryは全source・input／native／trace指紋、各契約と照準遷移・旧点witnessを残す。summary単体を完全nativeレポートとは扱わない。初版の「同時刻のskillも新しいframe照準を使う」という誤った検査、初期gauge満タンで充電窓が一度も開かなかった刺激、空descriptor commandのunit失敗を保持した。CPU正本を変更せず観測とfixtureを修正した。

最終の共通matrix packageでCPU85／control416（Windows専用1skip）を検査。full3052→compact1743の全残存byte一致、旧151のinput／golden／GPU source保持、生成cache必須hit／Slang0を確認する。新GPU0／Windows依頼0／raw削除0。手動aimのGPU受付は引き続き拒否、全キャラ0／モデルgap20／公開GPU閉鎖／UI CPU／全体目標未達。

```sh
python scripts/nikke_gpu.py reference --suite coordinate-aim-common --out /tmp/new-aim-reference.json
```

次はこの全契約を用いて、要求合流→調停後の照準bank→前半skillと後半physicalのcallerを共通Slangへ接続する。5anchorのうち予測clock・own buff expiry等が未接続なら、対応済み扱いにせず依存関係を解消する。
