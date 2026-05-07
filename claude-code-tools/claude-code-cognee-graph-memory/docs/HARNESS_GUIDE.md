# HARNESS_GUIDE — Claude Code × Cognee 自動蓄積ハーネス導入ガイド

## 【Claude Code × Cognee ノウハウ蓄積実用ツール】

**RAG は答えだけ。Cognee は経緯ごと。** Claude Code が「なぜそう決めたか」までをグラフ記憶する。
**「また同じこと言わせるな」を、終わらせよう！**

## このハーネスは何か

**Claude Code を使えば使うほど、あなた専用のノウハウが Cognee グラフ記憶に蓄積されていく仕組み** です。

- ユーザーの発言・AI の応答は hook によって自動的にグラフ記憶へ登録される
- 次のセッション以降、AI は作業着手前に必ずグラフ記憶を検索する
- 同じミスを繰り返さず、過去の決定・経緯・関連事実が芋づる式に引き出せる

単なるベクトル検索（RAG）では「該当チャンク」だけが返ります。Cognee はグラフ構造により、その決定の根拠・経緯・関連事実までを連結して返します。「なぜそう決めたか」「いつから」「何が関連するか」までが取り出せる、実用的なノウハウ蓄積ハーネスです。

---

## 仕組みの全体像

```
┌────────────────────────────────────────────────────────┐
│ Claude Code セッション                                  │
│                                                        │
│  ユーザー発言 ─────► UserPromptSubmit hook ────┐       │
│                                                ▼        │
│                                  ~/.claude/             │
│                                  cognee_pending_        │
│                                  remembers.jsonl        │
│                                  （キュー）              │
│                                                ▲        │
│  AI 応答完了 ─────► Stop hook ────────────────┘        │
│                                                         │
│  AI が作業前に                                          │
│  search(CHUNKS) ◄─── CLAUDE.md / rules で必須化         │
└────────────────────────┬───────────────────────────────┘
                         │
                         │ cognee-queue-flush skill が定期消化
                         │ (Claude Code 内蔵の /loop または CronCreate でスケジュール、
                         │  既存 MCP cognee サーバを共有・新プロセス spawn しない)
                         ▼
                ┌────────────────────┐
                │ Cognee グラフ記憶   │
                │ （永続）             │
                └────────────────────┘
```

---

## 導入手順（5ステップ）

### 前提

- 配布物本体（`docs/SETUP.md`）のセットアップが完了していること
- `claude mcp list` で `cognee` が登録済みであること
- `src/sample_src/load_sample.py` でサンプル投入が成功していること

### Step 1: ハーネスファイルを ~/.claude/ にコピー

```bash
# 配布物ルートから実行

# ルール（Cognee 利用方針）
cp harness/rules/cognee_memory_usage.md ~/.claude/rules/

# Hook（キュー追記のみ・v0.3.0 では flusher.py は廃止済）
cp harness/hooks/auto_remember_user_message.py ~/.claude/hooks/
cp harness/hooks/auto_remember_completion.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/auto_remember_user_message.py
chmod +x ~/.claude/hooks/auto_remember_completion.py

# Skill（キュー消化用・v0.2.x flusher.py の置き換え・Step 4 で必要）
mkdir -p ~/.claude/skills
cp -r harness/skills/cognee-queue-flush ~/.claude/skills/
```

> **v0.3.0 アーキテクチャの補足**: v0.2.x ではキュー消化を OS レベルの
> `cognee_remember_flusher.py`（cron 起動）が担っていました。v0.3.0 では
> `cognee-queue-flush` skill に置き換わり、**起動中の Claude Code セッション内で
> 動作・既存 MCP cognee サーバを共有** します。新たに `cognee-mcp` プロセスを
> spawn しないため、BUG-008（Ladybug DB ロック競合）が発生しません。

### Step 2: ~/.claude/settings.json をマージ

`harness/settings.example.json` の内容を、既存の `~/.claude/settings.json` に手動でマージしてください。

**特に重要なマージ対象**:
- `hooks.UserPromptSubmit` — ユーザー発言を自動記録
- `hooks.Stop` — AI 応答完了時の要点を自動記録
- `permissions.allow` — Cognee MCP ツール（search / remember 等）の自動許可

既存の hooks や permissions に追記する形でマージし、上書きしないように注意してください。

### Step 3: 各プロジェクトの CLAUDE.md にルールを追記

`harness/CLAUDE_md_sample.md` の内容を、ハーネスを有効化したいプロジェクトの `CLAUDE.md` 末尾に追記してください。

これにより、その AI（Claude Code）は **作業着手前に必ず Cognee グラフ記憶を検索する** ようになります。

### Step 4: cognee-queue-flush skill の定期実行を設定

hook はキューファイルに追記するだけで、実際の Cognee 登録は `cognee-queue-flush`
skill（既存 MCP cognee サーバ経由で remember 呼び出し・新プロセス spawn なし）が行います。

以下のいずれかで定期実行をスケジュール:

| 方法 | コマンド (Claude Code 内で入力) | 用途 |
|---|---|---|
| `/loop`（インタラクティブ） | `/loop 5m cognee-queue-flush` | 開発・テスト用。手軽に開始/停止できるがセッション終了で消える |
| `CronCreate`（セッション内永続） | `CronCreate(cron="*/5 * * * *", prompt="cognee-queue-flush", recurring=true)` | 常時稼働用。セッション内で最大 7 日有効 |

> **v0.3.0 で OS レベル cron を使わない理由**: OS レベル cron で起動すると
> その都度新しい `cognee-mcp` プロセスを spawn し、Claude Code セッションが
> すでに保持している MCP cognee サーバと衝突して BUG-008（Ladybug DB ロック競合）
> を引き起こします。Claude Code 内蔵スケジューラなら 1 プロセス内で完結するため
> 衝突しません（v0.3.0 設計上の必須要件）。

同じ理由で、CLI ヘルパー `src/sample_src/load_sample.py` および
`src/sample_src/delete_sample.py` は **Claude Code が起動していない状態** でのみ
実行してください（SETUP.md §2-5 参照）。

#### 1 回の起動で処理する件数のチューニング

デフォルトでは `cognee-queue-flush` skill は 1 回の起動で **キューの先頭 3 件まで**
処理し、残りは次回の起動に持ち越します。デフォルト値 3 は控えめな初期値です。
**1 回のスケジュール間隔内に何件処理できるかはユーザー環境に完全に依存します**
(CPU/GPU・VRAM・選択した LLM・cloud LLM の場合はネットワーク遅延)。

環境変数 `COGNEE_QUEUE_FLUSH_MAX_PER_RUN` で上限を変更できます:

```bash
# 例: 1 回の起動で最大 10 件処理する (cloud LLM・高速マシン向け)
export COGNEE_QUEUE_FLUSH_MAX_PER_RUN=10
```

シェル設定ファイル (`~/.bashrc`、`~/.zshrc` など) に追記すると、Claude Code 起動時に
自動的に反映されます。

**初期値の目安** (skill の報告 `(成功, 失敗, 残存)` を観察しつつ、必ず自分の環境に
合わせて調整してください):

| 構成 | 推奨値 |
|---|---|
| Cloud LLM (Claude / OpenAI / Gemini) | 10 〜 20 |
| ローカル Ollama・qwen2.5:14b・GPU (VRAM 8GB+) | 3 〜 5 (デフォルト 3) |
| ローカル Ollama・qwen2.5:14b・CPU のみ | 1 〜 2 |
| ローカル Ollama・小型モデル (qwen2.5:7b など) | 5 〜 10 |

値を高くしすぎると 1 回の drain がスケジュール間隔 (デフォルト 5 分) を超えて
次回発火と重なります。低すぎるとキューが drain よりも速く増える可能性があります。
**まずはデフォルト値で動かして、観察した動作を見て調整してください**。

#### Claude Code 再起動後も schedule を維持するには

`/loop` および `CronCreate` の登録は **1 つの Claude Code セッション内でのみ** 有効です。
Claude Code を終了 (VSCode で `Reload Window` 含む) すると schedule は消え、
再登録するまでキューの drain は止まります。

再起動後も schedule を維持するには `CronCreate` を `durable=true` で呼ぶ必要があります:

```
CronCreate(
    cron="*/5 * * * *",
    prompt="cognee-queue-flush",
    recurring=true,
    durable=true,   # <-- ここがポイント
)
```

`durable=true` を指定すると登録情報が `~/.claude/scheduled_tasks.json` に保存され、
次回 Claude Code 起動時に自動復元されます (再登録不要)。

> ⚠️ **`/loop` では schedule を永続化できません。** スラッシュコマンドには `durable`
> オプションがなく、永続化は `CronCreate` Tool 経由でしか実現できません。Tool は
> **Claude Code (AI) が実行するもので、ユーザーが直接タイプするものではありません**。
> 永続化が必要な場合は、Claude Code のチャットで一度だけ AI に依頼してください:
>
> > `CronCreate` を `cron="*/5 * * * *"`、`prompt="cognee-queue-flush"`、
> > `recurring=true`、`durable=true` で呼んでください。再起動後もキューの drain が
> > 続くように。
>
> AI が Tool を 1 回呼べば登録は `~/.claude/scheduled_tasks.json` に保存され、
> 以降は依頼不要です。

セッションをまたいで使うことが少なく、毎回 Claude Code を立ち上げ直す運用で問題なければ、
セッション内のみの `/loop 5m cognee-queue-flush` のほうが簡単です — セッションごとに
1 回タイプすることだけ覚えておいてください。

### Step 5: Claude Code を再起動

settings.json と hook を変更したので、既に起動中の Claude Code セッションには反映されません。

- VSCode Claude Code 拡張機能を使っている場合: VSCode を `Reload Window` で再起動
- ターミナル `claude` コマンド: 一度終了して再起動

接続確認:
```bash
claude mcp list
# cognee が ✓ Connected で表示されればOK
```

---

## 動作確認

### ハーネスが効いているかの確認

1. 何らかの発言を Claude Code に送る
2. `cat ~/.claude/cognee_pending_remembers.jsonl` を実行 → 発言が追記されていればOK
3. Claude Code 内で `cognee-queue-flush` skill を手動起動
   （`/cognee-queue-flush` または Skill ツール経由）
4. skill の実行サマリ（succeeded_count / failed_count）が表示され、
   `~/.claude/cognee_pending_remembers.jsonl` が消化（空または短く）されていればOK
5. Cognee 側で確認: Claude Code から `search("先ほどの発言の主題語", search_type="CHUNKS")` を呼ぶ → 該当ヒットがあればOK

### AI が search を呼ぶようになったかの確認

ハーネス導入前と導入後で、Claude Code に同じ作業を依頼した際の挙動を比較:

- 導入前: いきなり Edit/Bash を実行する
- 導入後: 最初に `mcp__cognee__search(...)` を呼び、その結果を踏まえて作業に入る

導入後の挙動になっていない場合は、CLAUDE.md への追記が反映されていない可能性があります。

---

## トラブルシューティング

### hook が動かない（キューファイルが更新されない）

- `~/.claude/settings.json` の `hooks.UserPromptSubmit` / `hooks.Stop` の構造が正しいか確認
- Claude Code を再起動したか確認（hook 変更は再起動必須）
- `python3 ~/.claude/hooks/auto_remember_user_message.py < /dev/null` で単独実行できるか確認

### skill がエラーで失敗する

- Claude Code チャットに表示される skill の実行サマリ
  （succeeded_count / failed_count とエラーメッセージ）を確認
- `~/.claude/cognee_failed_remembers.jsonl` に失敗エントリが退避されているので原因調査の参考に
- skill が配置されているか確認: `ls ~/.claude/skills/cognee-queue-flush/SKILL.md`
- Claude Code が skill を認識しているか確認:
  skill を `~/.claude/skills/` に配置した直後は、新しい Claude Code セッションが必要
- 配布物ルートのパスが見つからない場合は環境変数 `COGNEE_GRAPH_MEMORY_ROOT` を設定:
  ```bash
  export COGNEE_GRAPH_MEMORY_ROOT=/path/to/claude-code-cognee-graph-memory
  ```

### AI が search を呼んでくれない

- そのプロジェクトの `CLAUDE.md` に `harness/CLAUDE_md_sample.md` の内容が追記されているか確認
- CLAUDE.md は Claude Code が毎ターン読むため、再起動不要だが、新規セッション開始で反映される
- ルールが緩すぎる可能性 → `harness/rules/cognee_memory_usage.md` を `~/.claude/rules/` に配置すると詳細版が AI に効く

### キューが大量に溜まっている

- `cognee-queue-flush` skill が定期起動されていない可能性 →
  `/loop 5m cognee-queue-flush` がアクティブか、または
  `CronCreate(cron="*/5 * * * *", ...)` が登録されているか確認
- 1件あたり数秒〜数十秒かかるため、初回起動時は溜まっていることがある
- 手動消化: Claude Code 内で `cognee-queue-flush` skill を 1 度起動

---

## 関連ファイル

| ファイル | 役割 |
|---|---|
| `harness/CLAUDE_md_sample.md` | プロジェクト CLAUDE.md に追記するサンプル |
| `harness/rules/cognee_memory_usage.md` | `~/.claude/rules/` 配置用の詳細ルール |
| `harness/hooks/auto_remember_user_message.py` | UserPromptSubmit hook（発言キュー追記） |
| `harness/hooks/auto_remember_completion.py` | Stop hook（応答キュー追記） |
| `harness/skills/cognee-queue-flush/SKILL.md` | キュー消化 skill（既存 MCP cognee 経由・v0.2.x flusher.py の置き換え） |
| `harness/settings.example.json` | settings.json マージ用サンプル |

---

## このハーネスの効果（運用の積み上げ）

- 1日使用 → 数十件のノウハウが蓄積
- 1週間使用 → 数百件のノウハウが蓄積（過去の指摘・決定が引き出せる）
- 1ヶ月使用 → 数千件のノウハウが蓄積（あなた専用の AI ノウハウベースが完成）

**Claude Code を使えば使うほど、あなた専用の AI が育っていきます。**
