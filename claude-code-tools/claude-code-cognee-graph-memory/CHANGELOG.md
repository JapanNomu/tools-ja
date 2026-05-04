# Changelog

このプロジェクトの全ての注目すべき変更はこのファイルに記録されます。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
[Semantic Versioning](https://semver.org/lang/ja/spec/v2.0.0.html) に従います。

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
