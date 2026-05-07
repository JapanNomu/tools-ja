# Changelog

このプロジェクトの全ての注目すべき変更はこのファイルに記録されます。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
[Semantic Versioning](https://semver.org/lang/ja/spec/v2.0.0.html) に従います。

## [0.3.2] - 2026-05-07

### Changed

- ドキュメントクリーンアップの継続。配布物に同梱されていないスクリプトの設定例が `config/.env.example` に残っていたので削除しました。`harness/` 配下のコメント・docstring も軽微な表現修正を行っています。**コード・要件定義・設計書・テスト成果物には一切変更ありません。**

## [0.3.1] - 2026-05-07

### Changed

- **ドキュメントクリーンアップ: 配布物から開発プロジェクト内 ID を削除しました。** v0.3.0 配布物には開発プロジェクト内のみで通用する ID (障害 ID BUG-007 / BUG-008 / BUG-009、要件 ID FR08-* / NF08 / NF09、タスク ID V03-*) が `README.md` / `docs/SETUP.md` / `docs/GETTING_STARTED.md` / `docs/HARNESS_GUIDE.md` / `harness/skills/cognee-queue-flush/SKILL.md` に多数残存していました。これらは配布物受領者にとって参照先がなく意味不明なため、v0.3.1 ですべて削除し、周辺文を具体的な記述に書き換えました (例: 「BUG-008」 → 「Ladybug DB ロック競合エラー (`Could not set lock on file`)」)。1 箇所の開発プロジェクト内ドキュメント参照 (`プロジェクトドキュメント内の BUG-008 fix_plan`) は `CHANGELOG.md` の v0.3.0 エントリへの参照に置き換えました。**コード・要件定義・設計書・テスト成果物には一切変更ありません。**

## [0.3.0] - 2026-05-07

### Fixed

- **Ladybug DB の `Could not set lock on file` が発生しなくなりました** (Zenn 記事 v0.2.1 にて **uzuchi 様**よりご報告いただいた事象)。
  - **変更前 (v0.2.1)**: 別プロセスで動く `harness/hooks/cognee_remember_flusher.py` (`crontab -e` または `nohup ... --daemon` で起動) が、キュー drain のたびに **新たな `cognee-mcp` プロセスを spawn** していました。CLI ヘルパー `src/sample_src/load_sample.py` / `src/sample_src/delete_sample.py` / `src/knowledge_src/import_knowledge.py` も同様です。Claude Code を起動した状態では既に `cognee-mcp` を 1 つ保持しているため、2 つ目の spawn が Ladybug DB の non-blocking ロック (`fcntl(F_SETLK, F_WRLCK)`) に当たって即時失敗していました。
  - **変更後 (v0.3.0)**: 起動中の Claude Code セッション**内**で動く新 skill `harness/skills/cognee-queue-flush/SKILL.md` がキューを drain します。スケジュールは `/loop 5m cognee-queue-flush` (セッション内のみ) または `CronCreate(cron="*/5 * * * *", prompt="cognee-queue-flush", recurring=true, durable=true)` (`~/.claude/scheduled_tasks.json` に保存・再起動後も自動復元) で登録します。skill は **既存の** MCP cognee サーバに対して `mcp__cognee__remember` を呼ぶため、新しい `cognee-mcp` プロセスは一切作成されません。CLI ヘルパーは **Claude Code を起動していない状態** でのみ実行する規約とし、削除に関しては Claude Code 起動中でも安全に呼べる代替手段として `mcp__cognee__delete_dataset` を案内します。ご報告いただいた再現条件と同等の条件下で MCP `remember` / `search` / `delete_dataset` を累計 50 回以上呼び出して**ロック競合 0 回**を確認しています。

- **`mcp__cognee__remember` の失敗がキューからサイレントに削除される問題を修正しました。**
  - **変更前 (v0.2.1)**: cognee-mcp upstream は失敗時にも `is_error=False` を返し、本文に `Error:` 始まりの文字列を入れます。v0.2.x の flusher は戻り値を破棄していたため (`# result =` のコメントアウト)、失敗エントリも処理済として削除されデータロストが発生していました。
  - **変更後 (v0.3.0)**: 新 skill 内に 3 重失敗判定 (`is_error=True` / `content[*].text` が `Error:` 始まり / 例外発生) を実装。失敗エントリは `~/.claude/cognee_failed_remembers.jsonl` に退避し、キューにも残るため次回発火で再試行されます。

### Changed

- **Cognee バージョン 1.0.5 → 1.0.8**。`pip install "cognee[fastembed]==1.0.8"` で固定。cognee 1.0.7 / 1.0.8 には Ollama リグレッション (`test_llm_connection` が `/v1` なし URL を叩いて 404) があるため、`config/.env.example` に `LLM_ENDPOINT=http://localhost:11434/v1` (`/v1` 必須) と `COGNEE_SKIP_CONNECTION_TEST=true` を既定設定済み。
- **`cognee-queue-flush` skill が 1 回の発火で処理するキュー件数の上限を環境変数 `COGNEE_QUEUE_FLUSH_MAX_PER_RUN` で指定できるようになりました (デフォルト 3 件)**。1 件の `mcp__cognee__remember` 呼び出しは LLM や PC スペック次第で数秒〜数十秒かかり、1 回の drain がスケジュール間隔を超えると次回発火と重なるため、ユーザー環境に合わせて調整するための仕組みです。`docs/HARNESS_GUIDE.md` Step 4 と `docs/SETUP.md` §2-4 に目安値 (cloud LLM 10〜20 / qwen2.5:14b GPU 3〜5 / CPU のみ 1〜2 / 小型ローカルモデル 5〜10) を記載しています。
- **`docs/HARNESS_GUIDE.md` と `docs/SETUP.md` を全面改訂**: Step 1 の skill インストール手順、Step 4 の `/loop` / `CronCreate` 設定、「ライフタイム」列によるセッション内のみ vs `durable=true` 永続化の違いを明記。`harness/settings.example.json` も flusher 関連 hook と Bash 許可を削除し、skill 起動への参照に置換。

### Removed

- `harness/hooks/cognee_remember_flusher.py` および OS レベルの `crontab -e` / `nohup --daemon` 起動経路を削除。詳細は **マイグレーション** を参照。

### マイグレーション (v0.2.1 から)

1. v0.3.0 を取得します。
2. `docs/HARNESS_GUIDE.md` Step 1 を再実行 (hook 再コピー + 新 skill ディレクトリ `harness/skills/cognee-queue-flush` を `~/.claude/skills/` へコピー)。
3. 不要になった `~/.claude/hooks/cognee_remember_flusher.py` を削除し、`crontab -e` から `*/5 * * * * .../cognee_remember_flusher.py` 行を消去。
4. Claude Code を再起動 (新 skill を認識させるため)。
5. 新セッション内で schedule を 1 回だけ登録: `/loop 5m cognee-queue-flush` を入力する、または再起動後も維持したい場合は AI に `CronCreate(cron="*/5 * * * *", prompt="cognee-queue-flush", recurring=true, durable=true)` を実行してもらう (`durable=true` は AI 側 `CronCreate` Tool でしか指定できず、`/loop` スラッシュコマンドからは指定不可)。

### Known Issues

- **save_interaction は引き続き利用不可。** **cognee-mcp 0.5.4 が cognee 1.0.8 の `add_rule_associations` 関数を呼ぶ際に引数名 `context=...` を渡しますが、cognee 側はすでに引数名を `ctx=...` にリネーム済みのため、引数名不整合で呼び出しに失敗します**。対話テキストの即時永続化は `remember` を利用してください。upstream の cognee-mcp プロジェクトで追跡中。

### Special Thanks

- **uzuchi 様** — Zenn 記事 v0.2.1 のコメントで `Could not set lock on file` の事象と再現条件 (Windows ネイティブ Claude Code → `wsl.exe -d Ubuntu-24.04 -- python3 .../start_cognee_mcp.py` を stdio transport で登録・`shared_ladybug_lock` 未設定・Redis 未起動) を詳細に共有してくださったことが、v0.3.0 で実施したロック競合の根本対処およびサイレントデータロスト対処を含むアーキテクチャ全面改修の出発点となりました。ありがとうございます。

## [0.2.1] - 2026-05-04

### Changed
- コードスタイルのみの修正で、**動作変更なし**。v0.2.0 検証結果（UT 110 / IT 6
  / ET 4 / ST 4 全件PASS、qwen2.5:14b マトリクス検証 8 ツール × 5 回）は
  ロジック未変更のため引き続き有効。
- cognee-integrations のコーディング規約（Ruff: `line-length = 100`、
  `select = ["E", "F", "I", "W"]`、`target-version = "py310"`）に
  準拠するため lint 修正を適用:
  - `harness/hooks/auto_remember_completion.py`: F401 — 未使用の
    `import os` をコメントアウトし import ブロック外に移動
  - `harness/hooks/auto_remember_user_message.py`: F401 — 未使用の
    `import os` と `import subprocess` をコメントアウトし import
    ブロック外に移動
  - `harness/hooks/cognee_remember_flusher.py`: F841 — `result =`
    の代入をコメントアウト（関数呼び出しは保持）。E501 — argparse
    `--interval` 行を 100 文字以内に改行
  - `src/knowledge_src/import_knowledge.py`: E501 — logger と argparse
    の 3 箇所を改行で 100 文字以内に
  - `src/main_src/import_to_graph.py`: I001 — `urllib.error` と
    `urllib.request` の import 順序をアルファベット順に入れ替え。
    E501 — argparse description と help を改行で 100 文字以内に

### Why
- cognee-integrations への寄稿候補としてツールキットを準備（cognee 共同創業者
  Vasilije Markovic 氏から X 上で「機能拡張の PR を送ってきていい」との招待を
  受けたため）。cognee-integrations の CI は上記 Ruff lint ルールを強制する
  ため、PR レビュー時に CI で却下されないよう事前に対応した。

## [0.2.0] - 2026-05-04

### Added
- `knowledge/sample_knowledge/05_graph_memory_operations.md` を新規追加。
  Cognee グラフ記憶の運用ノウハウ（cognify を呼ぶタイミング、remember と
  save_interaction の使い分け、search 種別の選択、recall のオートルーティング、
  forget_memory・improve・prune の使用法）を記述したサンプル投入用ファイル。
  これに伴い同梱サンプルが 4 ファイルから 5 ファイルに増えた。

### Changed
- **Cognee バージョンを 1.0.3 → 1.0.5 にアップグレード**しました。Cognee 1.0.4 で
  グラフDBが KuzuDB から **Ladybug DB** に置換された点に追従しています。
  - 依存パッケージ: `kuzu==0.11.3` → `ladybug==0.16.0`（自動置換・後方互換エイリアスあり）
  - 動作実証 Cognee バージョン: 1.0.5
  - cognee-mcp バージョン: 0.5.4（変化なし）
- ドキュメント全般で **「KuzuDB」表記を「Ladybug DB」**に修正しました。
  - `README.md`（特徴説明・技術スタック表）
  - `config/.env.example`（COGNEE_DATA_PATH コメント・データ保存先説明）
  - `docs/SETUP.md`（動作確認バージョン・固定バージョン例）
  - `docs/GETTING_STARTED.md`（検証Cogneeバージョン・応答時間実測値）
- 同梱サンプルファイル数の記述を 4 → 5 に更新。
  - `README.md`（ディレクトリ構成セクション）
  - `docs/GETTING_STARTED.md`（投入ログ表示 `[N/M]` を含む）
- `knowledge/sample_knowledge/03_design_decisions.md` の設計判断記述を整理。
  KuzuDB/LanceDB/FastEmbed は Cognee 内蔵のため自動的に使われるものであり、
  ユーザー側の選定対象ではない。「Cognee を採用した理由」に統合し、
  グラフDBは v0.2.0=Ladybug DB / v0.1.x=KuzuDB と注記した。
- `knowledge/sample_knowledge/04_common_errors.md` のエラー対処記述で、
  ローカルLLM の例示を `llama3.1:8b` から `qwen2.5:14b`（v0.2.0 で唯一の
  動作確認済みローカルLLM）に統一。
- `harness/rules/cognee_memory_usage.md` の recall 失敗条件記述を、
  「`llama3.1:8b` では失敗することがある」から「`qwen2.5:14b` 以外の
  ローカルLLM では失敗することがある」に更新。

### Fixed（v0.1.10〜v0.1.12 から残存していたソースコード既存欠陥の修正）
- `src/main_src/import_to_graph.py`:
  - `list_targets()` から、TARGET_MAP に存在しない `comments` ターゲットの
    表示行を削除（v0.1.10 から残存していた誤表示）
  - `check_ollama()` を `LLM_PROVIDER=ollama` の時のみ実行するよう修正
    （クラウドAPI 設定時に意味なく失敗していた）
  - `--dry-run` 時は `check_ollama()` をスキップするよう修正
    （ファイル一覧表示だけのモードで Ollama 接続不要）
- `src/knowledge_src/import_knowledge.py`:
  - `check_ollama()` に同様の `LLM_PROVIDER=ollama` チェックを追加
- `harness/hooks/auto_remember_user_message.py`:
  - docstring の「簡易運用版を提供」「本サンプルでは後者の簡易運用版」記述が
    実装（キュー方式のみ）と矛盾していた点を修正
- `harness/hooks/cognee_remember_flusher.py`:
  - キュー処理の `remaining` 計算条件を `not line.strip()` → `line.strip()` に修正
    （失敗データが意図せずキューから消える内部バグ。`failed.jsonl` には退避済の
    ためデータ消失はないが、再投入の起点であるキューの内容が誤っていた）
  - `remember_via_mcp()` 内の不要な `sys.path.insert(main_src)` を削除
    （fastmcp は配布物 venv の site-packages から直接インポート可能）

### Verified（v0.2.0 で実証）
- **qwen2.5:14b（num_ctx=8192）× Ladybug DB 環境で 35/40 ✅** を実証
  - remember 5/5 ✅・search(CHUNKS) 5/5 ✅・search(GRAPH_COMPLETION) 5/5 ✅・recall 5/5 ✅
  - cognify 5/5 ✅・improve 5/5 ✅・forget_memory 5/5 ✅
  - **save_interaction 0/5 ❌**（既知の制限事項・後述）
- **Ladybug DB（Cognee 1.0.4で導入）により graph traversal が高速化**し、
  qwen2.5:14b で実用速度を達成（v0.1.x の KuzuDB 環境より体感大幅改善）。
  - search(CHUNKS): 平均 3.2秒（決定論的・LLM不使用）
  - search(GRAPH_COMPLETION): 平均 14.6秒（範囲 12〜18秒）
  - recall（Q-A・TEMPORAL routing）: 20〜24秒
  - recall（Q-B・GRAPH_COMPLETION_COT routing）: 154〜156秒
  - improve / forget_memory: 全件即時（数秒以下）

### Known Issues（既知の制限事項）
- **save_interaction が利用不可**（cognee-mcp 0.5.4 と cognee 1.0.5 のAPI不整合）
  - エラー: `add_rule_associations() got an unexpected keyword argument 'context'`
  - 原因: cognee 1.0.5 で `add_rule_associations` の引数が `context` → `ctx` にリネームされたが、
    cognee-mcp 0.5.4 が未追従（upstream `topoteretes/cognee` の main branch も同状態）
  - 代替案: 会話ペアの永続記憶への即時保存は `remember` で代替可能

### Migration（v0.1.x からのアップグレード）
- 1.0.3 のグラフDB（KuzuDB）データはCognee 1.0.4起動時の自動マイグレーション機能で
  Ladybug 形式に変換されます。
- 既存データを保持したい場合: `pip install -U "cognee[fastembed]==1.0.5"` でアップグレード
  → 初回 `cognee` 起動時に自動移行
- 既存データをリセットしてよい場合: `forget_memory(everything=True)` で全削除後、
  Cognee 1.0.5 環境で再 cognify

## [0.1.12] - 2026-05-03

### Fixed
- `README.md` および `docs/GETTING_STARTED.md` のハードウェア表記を
  **GPUモデル名ベース** から **VRAM 容量ベース** に修正しました。
  従来「RTX 4070 12GB 以上」と書かれていましたが、ノートPC版の
  RTX 4070 は VRAM 8GB しかないため、自分のノートPCが要件を満たしている
  と誤解する読者が出る恐れがありました。推奨表記を「VRAM 12GB 以上の GPU」
  に変更し、ノートPC版に関する注意書きも追加しています。動作確認下限は
  「NVIDIA GeForce RTX 4060 Laptop GPU（VRAM 8GB）」として、実機の正確な
  名称で記載するように修正しました。
- `CHANGELOG.md` を整理し、公開後の変更だけを残しました（v0.1.10 以降）。
  公開前の v0.1.0〜v0.1.9 は内部開発履歴のため、公開ノイズとして除去
  しています。

## [0.1.11] - 2026-05-02

### Changed
- `config/.env.example` のデフォルト LLM を `qwen2.5:14b`（num_ctx=8192）に
  切り替えました。Claude API / OpenAI API への切り替え方法もコメントで併記
  しています。
- `docs/GETTING_STARTED.md` に「推奨LLM・推奨環境」セクションを新設しました。
  - クラウドAPI（Claude / OpenAI）を **強く推奨**（公式 structured output
    サポートにより信頼性が高い）。
  - ローカルLLM運用は **VRAM 12GB 以上の GPU** + **qwen2.5:32b 以上** を推奨
    （14B 以上が最低ライン）。
- `src/main_src/import_to_graph.py` および `src/knowledge_src/import_knowledge.py`
  の `LLM_MODEL` を `config/.env` から動的に読み込む実装に変更しました
  （これまでは `llama3.1:8b` がハードコードされていました）。
- `docs/GETTING_STARTED.md` の `llama3.1:8b` 前提の記述を `qwen2.5:14b` ／
  クラウドAPI 併記へ書換しました（サンプル登録失敗時の代替モデル例・
  recall 失敗時の注記・トラブルシューティング）。

## [0.1.10] - 2026-05-02

### Added
- 初回公開リリース。Claude Code に Cognee グラフ記憶を追加するモジュール。
  - `src/main_src/start_cognee_mcp.py` — MCP サーバー起動スクリプト
  - `src/main_src/import_to_graph.py` — グラフ記憶への投入
  - `src/sample_src/load_sample.py` / `delete_sample.py` — 同梱サンプル投入・削除
  - `src/knowledge_src/split_knowledge.py` / `import_knowledge.py` — 大量ノウハウ初期投入用
  - `docs/SETUP.md` / `docs/GETTING_STARTED.md` / `docs/HARNESS_GUIDE.md` —
    環境構築・動作確認・自動蓄積ハーネス導入ガイド
  - `knowledge/sample_knowledge/` — 動作確認用同梱サンプル（4ファイル）
  - `harness/` — Claude Code × Cognee 自動蓄積ハーネス（任意機能）
  - 完全ローカル動作可能（Ollama + FastEmbed・外部APIキー不要）
