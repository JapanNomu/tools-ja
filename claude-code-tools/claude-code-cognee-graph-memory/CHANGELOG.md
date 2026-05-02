# Changelog

このプロジェクトの全ての注目すべき変更はこのファイルに記録されます。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
[Semantic Versioning](https://semver.org/lang/ja/spec/v2.0.0.html) に従います。

## [0.1.10] - 2026-05-02

### Changed
- リポジトリ履歴をクリーンに整理しました。v0.1.0〜v0.1.9 の旧履歴は
  内部プロジェクト識別子・ファイル整理過程の痕跡を含んでいたため、
  GitHub 上のリポジトリを再作成し、v0.1.10 を **クリーンな初回公開リリース**
  としました。本配布物の機能・構造は v0.1.9 と同等で、**履歴のみが差し替え**
  されています。
- 旧履歴に含まれていた変更内容のサマリは本 CHANGELOG の `[0.1.0]`〜`[0.1.9]`
  エントリに保持しています（記録としての透明性を保つため）。

## [0.1.9] - 2026-05-02

### Changed
- 日本語版を `JapanNomu/tools-ja` リポジトリで独立公開する形に整理しました。
- 英語版（`JapanNomu/tools`）と並行リリースとし、それぞれの言語で完結した
  形（ドキュメント・ソースコメント・設定ファイルコメント）で配布します。

## [0.1.8] - 2026-05-02

### Added
- `harness/` ディレクトリを新設しました。Claude Code × Cognee 自動蓄積
  ハーネスとして、ユーザー発言・AI 応答を Cognee グラフ記憶に登録し、
  CLAUDE.md / `~/.claude/rules/` で「作業前に必ず検索」ルールを強制します。
  同梱内容：
  - `harness/CLAUDE_md_sample.md` — プロジェクト CLAUDE.md に追記するサンプル
  - `harness/rules/cognee_memory_usage.md` — `~/.claude/rules/` 配置用の詳細ルール
  - `harness/hooks/auto_remember_user_message.py` — UserPromptSubmit hook
  - `harness/hooks/auto_remember_completion.py` — Stop hook
  - `harness/hooks/cognee_remember_flusher.py` — キュー消化（cron 推奨）
  - `harness/settings.example.json` — settings.json マージ用サンプル
- `docs/HARNESS_GUIDE.md` を新設しました。ハーネスの導入手順を記載しています。
- `README.md` にハーネス紹介とキャッチコピー
  （「RAG は答えだけ。Cognee は経緯ごと。」）を追記しました。

## [0.1.7] - 2026-05-02

### Added
- `docs/GETTING_STARTED.md` の3箇所（体験シナリオ A・Step 3・ツール一覧）に
  「`recall` 失敗時は `search(CHUNKS)` で代替」の注記を追加しました。
  llama3.1:8b では `recall` が「LLM フォーマットエラー」で失敗することがある
  ため、既存のトラブルシューティング項目（「LLMフォーマットエラーで recall が失敗する」）
  への導線を本文側から張り、初見ユーザーが詰まらないようにしました。

## [0.1.6] - 2026-05-02

### Added
- `docs/SETUP.md` Section 2-3「セットアップ後の動作確認」に「Claude Code が
  既起動の場合は再起動が必要」注意書きを追加しました。`claude mcp add` で
  登録した設定は既起動セッションには反映されないため、VSCode Claude Code
  拡張機能・ターミナル `claude` セッションを再起動する必要があります。
  接続確認方法3つ（`claude mcp list`・VSCode「MCP servers」パネル・`/mcp`）も
  併記しました。

## [0.1.5] - 2026-05-02

### Fixed
- `src/main_src/start_cognee_mcp.py`: cognee-mcp 起動前に `config/.env` を
  プロセス環境変数に読み込む処理を追加しました。修正前は子プロセスが
  `LLM_API_KEY` `LLM_ENDPOINT` `SYSTEM_ROOT_DIRECTORY` 等を持たない状態で
  起動するため、MCP 経由の `cognify` 呼び出しが `LLMAPIKeyNotSetError
  (Status 422)` で失敗していました。stdlib のみで実装し、追加依存はありません。

## [0.1.4] - 2026-05-02

### Added
- `docs/GETTING_STARTED.md` にサンプル登録失敗時の対処を追記しました。
  LLM 応答エラーで失敗した場合は `delete_sample.py` でクリアして再実行する
  手順を案内します。

## [0.1.3] - 2026-05-02

### Changed
- `docs/SETUP.md` Section 4 の `COGNEE_DATA_PATH` 記載を「必須」から「任意」に
  修正しました。既定値（`./data/cognee`）のままで動作するため、変更したい
  場合のみ設定する旨を明記しました。

## [0.1.2] - 2026-05-02

### Changed
- `docs/SETUP.md`: MCP 登録時に **絶対パス必須** であることを明記しました。
  相対パスで登録すると Claude Code が起動時の作業ディレクトリ基準でパスを
  解決するため、配布物ディレクトリ以外から `claude` を起動した時に接続でき
  なくなります。

## [0.1.1] - 2026-05-01

### Fixed
- `docs/SETUP.md`: 誤った `pip install` コマンドと「3つの値」の表記を修正しました。

## [0.1.0] - 2026-05-01

### Added
- 初回リリース。Claude Code に Cognee グラフ記憶を追加するモジュール。
  - `src/main_src/start_cognee_mcp.py` — MCP サーバー起動スクリプト
  - `src/main_src/import_to_graph.py` — グラフ記憶への投入
  - `src/sample_src/load_sample.py` / `delete_sample.py` — 同梱サンプル投入・削除
  - `src/knowledge_src/split_knowledge.py` / `import_knowledge.py` — 大量ノウハウ初期投入用
  - `docs/SETUP.md` / `docs/GETTING_STARTED.md` — 環境構築・動作確認ガイド
  - `knowledge/sample_knowledge/` — 動作確認用同梱サンプル（4ファイル）
  - 完全ローカル動作（Ollama + FastEmbed・外部API不要・追加費用ゼロ）
