# Changelog

このプロジェクトの全ての注目すべき変更はこのファイルに記録されます。

形式は [Keep a Changelog](https://keepachangelog.com/ja/1.1.0/) に基づいており、
[Semantic Versioning](https://semver.org/lang/ja/spec/v2.0.0.html) に従います。

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
