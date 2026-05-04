# Claude Code + Cognee グラフ記憶システム

**Version**: 0.2.1  
**動作実証 Cognee バージョン**: 1.0.5（Ladybug DB対応）

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
- **グラフ＋ベクトル検索** — Ladybug DB（グラフ）+ LanceDB（ベクトル）による高精度な想起
- **役割別フォルダ構成** — 本番運用・サンプル・ナレッジ初期投入をフォルダで分離

---

## Ladybug DB による速度向上（v0.2.0 実測値）

Cognee 1.0.4 で導入された **Ladybug DB** によりグラフ走査が高速化され、qwen2.5:14b（num_ctx=8192）でも実用速度を達成しました（v0.1.x の KuzuDB 環境より体感大幅改善）。

| ツール | 応答時間 | 備考 |
|---|---|---|
| `search(CHUNKS)` | 平均 3.2秒（範囲 2〜5秒） | 決定論的・LLM不使用 |
| `search(GRAPH_COMPLETION)` | 平均 14.6秒（範囲 12〜18秒） | LLM推論あり・実用速度 |
| `recall`（Q-A・TEMPORAL routing） | 20〜24秒 | 即時応答クラス |
| `recall`（Q-B・GRAPH_COMPLETION_COT routing） | 154〜156秒 | Chain-of-Thought 推論で長時間だが精度極高 |
| `improve` | 全件即時（数秒以下） | session_idsなしモード |
| `forget_memory` | 全件即時 | dataset指定/everything=True 両モード |
| `remember`（cognify同期実行） | 平均 92秒（範囲 44〜237秒） | エンティティ抽出含む |
| `cognify`（バックグラウンド処理） | 平均 145秒（範囲 99〜232秒） | 長文ドキュメント・MCP timeout回避のためバックグラウンド |

検証環境: NVIDIA GeForce RTX 4060 Laptop GPU（VRAM 8GB）/ RAM 32GB / qwen2.5:14b（num_ctx=8192）/ Cognee 1.0.5（Ladybug DB）

---

## 制限事項（v0.2.0 既知の問題）

- **`save_interaction` ツールは利用不可**
  - エラー: `add_rule_associations() got an unexpected keyword argument 'context'`
  - 原因: cognee-mcp 0.5.4 と cognee 1.0.5 の API 不整合（cognee 1.0.5 で引数 `context` → `ctx` にリネームされたが、cognee-mcp が未追従）
  - 代替案: 会話ペアを永続記憶に即時保存したい場合は `remember(data="User: ... / Assistant: ...")` を使用

その他のツール（`remember` / `search` / `recall` / `cognify` / `improve` / `forget_memory` 等）は v0.2.0 で完全動作を実証済みです。

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
| Ollama | 最新版（ローカルLLM運用時）|
| LLM | qwen2.5:14b（num_ctx=8192）— ローカル運用デフォルト。本番運用にはクラウドAPI（Claude / OpenAI）を強く推奨 |
| Claude Code | 最新版 |

### 推奨スペック

| 運用形態 | GPU | メモリ | LLM |
|---------|-----|--------|-----|
| **クラウドAPI（強く推奨）** | 不要 | 16GB以上 | claude-sonnet-4-6 / gpt-4o 等 |
| ローカルLLM（推奨） | VRAM 12GB 以上の GPU（※ノートPC版 RTX 4070 は VRAM 8GB なので不可・RTX 4070 デスクトップ版 / 4070 SUPER / 4070 Ti / 4080 等が該当） | 32GB以上 | qwen2.5:32b 以上 |
| ローカルLLM（動作確認下限） | NVIDIA GeForce RTX 4060 Laptop GPU（VRAM 8GB） | 32GB | qwen2.5:14b — Ladybug DB環境下で実用速度（応答時間の実測値は本README上部「Ladybug DB による速度向上」表を参照） |

詳細は `docs/GETTING_STARTED.md`「推奨LLM・推奨環境」を参照してください。

### 技術スタック

| 技術 | 詳細 |
|------|------|
| グラフ記憶エンジン | Cognee |
| LLM（エンティティ抽出） | qwen2.5:14b（デフォルト・ローカル）/ Claude API / OpenAI API |
| LLM実行基盤 | Ollama（ローカル）またはクラウドAPI |
| グラフDB | Ladybug DB（Cognee内蔵・1.0.4でKuzuDBから置換）|
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
    ├── sample_knowledge/         同梱サンプルデータ（5ファイル）
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
