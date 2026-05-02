# Claude Code + Cognee グラフ記憶システム

**Version**: 0.1.10

Claude Codeにグラフ記憶を追加するモジュールです。セッションをまたいで作業の記憶（ルール・教訓・設計決定・障害記録）を蓄積し、後のセッションで引き出せるようにします。

---

### 【Claude Code × Cognee ノウハウ蓄積実用ツール】

**RAG は答えだけ。Cognee は経緯ごと。** Claude Code が「なぜそう決めたか」までをグラフ記憶する。
**「また同じこと言わせるな」を、終わらせよう！**

`harness/` 同梱の自動蓄積ハーネスを使えば、Claude Code を使えば使うほど、あなた専用のノウハウが Cognee グラフ記憶に貯まり、決定・経緯・関連事実が芋づる式に引き出せます。詳細は `docs/HARNESS_GUIDE.md` を参照してください。

---

## なぜCognee MCPだけでは使えないか

1. **Cognee MCPは「ファイルパス」か「テキスト」しか受け付けない** — Claude Codeの作業ログ・会話テキストを自動的にグラフ記憶に投入する仕組みがない
2. **`import_to_graph.py` がその橋渡し** — `~/.claude/rules/` や任意のディレクトリのファイルをCogneeに投入できる
3. **`start_cognee_mcp.py` がClaude CodeとCogneeをつなぐ** — MCPサーバーとして登録しないとClaude Codeのツールとして使えない

---

## 特徴

- **完全ローカル動作** — Ollama + FastEmbed。外部APIキー不要・追加費用ゼロ
- **セッション横断** — Claude Codeのどのセッションからでも同一グラフ記憶にアクセス
- **グラフ＋ベクトル検索** — KuzuDB（グラフ）+ LanceDB（ベクトル）による高精度な想起
- **役割別フォルダ構成** — 本番運用・サンプル・ナレッジ初期投入をフォルダで分離

---

## 読む順番

| 順番 | ドキュメント | 内容 |
|---|---|---|
| 1 | この `README.md` | 全体概要・前提条件・ディレクトリ構成 |
| 2 | `docs/SETUP.md` | 環境構築手順（venv作成・Ollama導入・MCP登録） |
| 3 | `docs/GETTING_STARTED.md` | 動作確認・使い方・自分のノウハウ投入手順 |
| 4 | `docs/HARNESS_GUIDE.md` | 自動蓄積ハーネス導入手順（任意・強く推奨） |

---

## 前提条件

### 動作確認済み環境

| 項目 | 値 |
|------|---|
| OS | Linux（Ubuntu 22.04以降）/ WSL2 |
| Python | 3.12以上 |
| Ollama | 最新版 |
| LLMモデル | llama3.1:8b（64Kコンテキスト）|
| Claude Code | 最新版 |

### 推奨スペック

グラフ記憶にはLLMを使ったエンティティ抽出が必要です。Ollamaでローカルに実行するため、以下のスペックを推奨します。

| 項目 | 推奨スペック |
|------|-------------|
| GPU | RTX 4060（8GB VRAM）相当以上 |
| メモリ | 32GB RAM以上 |

> 動作検証環境: RTX 4060（8GB VRAM）+ 32GB RAM

### 技術スタック

| 技術 | 詳細 |
|------|------|
| グラフ記憶エンジン | Cognee |
| LLM（エンティティ抽出） | Llama 3.1 8B（64Kコンテキスト）|
| LLM実行基盤 | Ollama |
| グラフDB | KuzuDB（Cognee内蔵）|
| ベクトルDB | LanceDB（Cognee内蔵）|
| 埋め込みモデル | FastEmbed all-MiniLM-L6-v2 |

---

## ディレクトリ構成

```
配布物のルート/
├── README.md                     ← このファイル
├── LICENSE                       MITライセンス
│
├── config/
│   └── .env.example              環境変数テンプレート（コピーして config/.env に）
│
├── docs/
│   ├── SETUP.md                  環境構築手順
│   ├── GETTING_STARTED.md        動作確認・使い方
│   └── HARNESS_GUIDE.md          自動蓄積ハーネス導入手順
│
├── harness/                      Claude Code × Cognee 自動蓄積ハーネス（任意・強く推奨）
│   ├── CLAUDE_md_sample.md       プロジェクトCLAUDE.mdに追記するサンプル
│   ├── rules/
│   │   └── cognee_memory_usage.md   ~/.claude/rules/ 配置用の詳細ルール
│   ├── hooks/
│   │   ├── auto_remember_user_message.py    UserPromptSubmit hook
│   │   ├── auto_remember_completion.py      Stop hook
│   │   └── cognee_remember_flusher.py       キュー消化スクリプト（cron推奨）
│   └── settings.example.json     ~/.claude/settings.json マージ用
│
├── src/
│   ├── main_src/                 本番運用（Claude Code稼働中に動く）
│   │   ├── start_cognee_mcp.py   MCPサーバー起動スクリプト
│   │   └── import_to_graph.py    本番投入用（Claude Codeから呼ばれる）
│   ├── sample_src/               サンプル関連
│   │   ├── load_sample.py        同梱サンプル投入
│   │   └── delete_sample.py      同梱サンプル削除
│   └── knowledge_src/            ユーザーノウハウ初期投入（cognify失敗対策・小分け実行）
│       ├── split_knowledge.py    分割（H2見出しごと）
│       └── import_knowledge.py   投入（リトライ付き）
│
└── knowledge/
    ├── sample_knowledge/         同梱サンプルデータ（4ファイル）
    ├── user_knowledge/           ユーザーノウハウ元データ置き場（README参照）
    └── user_chunks/              分割後の中間ファイル置き場（自動生成）
```

---

## クイックスタート

1. `docs/SETUP.md` を参照してセットアップ
2. `src/venv/bin/python3 src/sample_src/load_sample.py` でサンプルデータを投入
3. `docs/GETTING_STARTED.md` の質問例を試す
4. `docs/HARNESS_GUIDE.md` を参照してハーネスを有効化（**強く推奨**。これによりノウハウが自動蓄積される）

自分のノウハウを使う場合は `docs/GETTING_STARTED.md` の「Step 4: ユーザー自身のノウハウを大量に投入する」を参照。

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 JapanNomu
