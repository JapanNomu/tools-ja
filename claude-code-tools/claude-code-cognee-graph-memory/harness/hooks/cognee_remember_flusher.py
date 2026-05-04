#!/usr/bin/env python3
"""
Cognee remember キューフラッシャー

auto_remember_user_message.py / auto_remember_completion.py が
~/.claude/cognee_pending_remembers.jsonl に追記したエントリを読み出し、
Cognee MCP の remember を実行してグラフ記憶に永続登録する。

UserPromptSubmit / Stop hook 内で MCP 呼び出しを直接行うと、
AI のターン進行が遅延する。そのため hook 側はファイル追記だけに留め、
このフラッシャーが定期的に・別プロセスで・順次登録する設計。

実行方法:
- 単発実行: python3 cognee_remember_flusher.py
- 常駐実行: nohup python3 cognee_remember_flusher.py --daemon &
- cron 実行（5分毎）:
    */5 * * * * /usr/bin/python3 /home/youruser/.claude/hooks/cognee_remember_flusher.py

依存:
- 配布物のセットアップが完了していること
- 環境変数 COGNEE_GRAPH_MEMORY_ROOT に配布物ルートのパスが設定されているか、
  または ~/tools/claude-code-tools/claude-code-cognee-graph-memory に配置されていること

設計判断:
- キュー読み出しは「行ごとに処理 → 成功したら削る」方式
- 失敗した行は ~/.claude/cognee_failed_remembers.jsonl に退避（後で再投入可能）
- 同時実行を防ぐため flock でロック
"""
import argparse
import asyncio
import fcntl
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

QUEUE_PATH = Path.home() / ".claude" / "cognee_pending_remembers.jsonl"
FAILED_PATH = Path.home() / ".claude" / "cognee_failed_remembers.jsonl"
LOCK_PATH = Path.home() / ".claude" / "cognee_flusher.lock"
LOG_PATH = Path.home() / ".claude" / "cognee_flusher.log"

# 配布物ルートの探索パス（環境変数 > 既定パス）
DEFAULT_ROOT_CANDIDATES = [
    Path(os.environ.get("COGNEE_GRAPH_MEMORY_ROOT", "")),
    Path.home() / "tools" / "claude-code-tools" / "claude-code-cognee-graph-memory",
]


def find_project_root() -> Path | None:
    for p in DEFAULT_ROOT_CANDIDATES:
        if p and p.exists() and (p / "src" / "main_src" / "import_to_graph.py").exists():
            return p
    return None


def log(msg: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {msg}\n")


async def remember_via_mcp(project_root: Path, data: str, dataset_name: str) -> bool:
    """
    fastmcp StdioTransport 経由で cognee MCP の remember を呼び出す。
    成功時 True、失敗時 False。
    """
    try:
        # fastmcp は配布物の venv に入っている前提でインポート
        from fastmcp import Client
        from fastmcp.client.transports import StdioTransport

        env = os.environ.copy()
        env_path = project_root / "config" / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()

        transport = StdioTransport(
            command=str(project_root / "src" / "venv" / "bin" / "python3"),
            args=[str(project_root / "src" / "main_src" / "start_cognee_mcp.py")],
            env=env,
        )

        async with Client(transport) as client:
            result = await client.call_tool(
                "remember",
                {"data": data, "dataset_name": dataset_name},
            )
            log(f"OK: dataset={dataset_name} len={len(data)}")
            return True
    except Exception as e:
        log(f"FAIL: {type(e).__name__}: {e}")
        return False


def acquire_lock():
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    fp = LOCK_PATH.open("w")
    try:
        fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fp
    except BlockingIOError:
        return None


def append_failed(entry: dict) -> None:
    FAILED_PATH.parent.mkdir(parents=True, exist_ok=True)
    with FAILED_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


async def flush_once() -> None:
    if not QUEUE_PATH.exists():
        return

    project_root = find_project_root()
    if not project_root:
        log("ERROR: claude-code-cognee-graph-memory project root not found")
        return

    # キュー読み出し → 全件試行 → 成功分は削除
    lines = QUEUE_PATH.read_text(encoding="utf-8").splitlines()
    if not lines:
        return

    succeeded_indices = set()
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            succeeded_indices.add(i)
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            log(f"SKIP malformed line: {line[:80]}")
            succeeded_indices.add(i)
            continue

        ok = await remember_via_mcp(
            project_root,
            entry["data"],
            entry.get("dataset_name", "main_dataset"),
        )
        if ok:
            succeeded_indices.add(i)
        else:
            append_failed(entry)

    # 失敗した有効データはキューに残す（成功分は削除・空行は捨てる・failed.jsonl にも退避済）
    remaining = [
        line for i, line in enumerate(lines)
        if i not in succeeded_indices and line.strip()
    ]
    if remaining:
        QUEUE_PATH.write_text("\n".join(remaining) + "\n", encoding="utf-8")
    else:
        QUEUE_PATH.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true", help="常駐モードで一定間隔で繰り返し実行")
    parser.add_argument("--interval", type=int, default=60, help="--daemon 時のインターバル秒（既定60）")
    args = parser.parse_args()

    lock = acquire_lock()
    if not lock:
        log("Another flusher is already running. Exit.")
        sys.exit(0)

    if args.daemon:
        while True:
            asyncio.run(flush_once())
            time.sleep(args.interval)
    else:
        asyncio.run(flush_once())


if __name__ == "__main__":
    main()
