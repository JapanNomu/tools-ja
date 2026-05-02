"""
分割済みノウハウファイル（user_chunks/）をCogneeグラフ記憶に投入する。

split_knowledge.py で分割したファイルを1件ずつCognee MCPサーバー経由で投入する。
1件投入後にcognify結果を確認し、status=errored の場合は最大3回までリトライする。

使用方法:
    cd <配布用のルートディレクトリ>
    src/venv/bin/python3 src/knowledge_src/import_knowledge.py
    src/venv/bin/python3 src/knowledge_src/import_knowledge.py --dry-run

入力:  knowledge/user_chunks/  配下の .md ファイル
出力:  Cognee の user_knowledge データセット
"""
import argparse
import asyncio
import json
import logging
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
ENV_PATH = PROJECT_ROOT / "config" / ".env"
MCP_COMMAND = str(PROJECT_ROOT / "src" / "main_src" / "start_cognee_mcp.py")
INPUT_DIR = PROJECT_ROOT / "knowledge" / "user_chunks"
DATASET_NAME = "user_knowledge"
MAX_RETRY = 3


def check_ollama() -> None:
    """Ollama 起動確認と llama3.1:8b モデル存在確認"""
    url = "http://localhost:11434/api/tags"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        logger.error("Ollama に接続できません: %s", e)
        logger.error("'ollama serve' を実行してから再試行してください")
        sys.exit(1)
    except Exception as e:
        logger.error("Ollama 接続チェックで予期しないエラー: %s", e)
        sys.exit(1)

    model_names = [m.get("name", "") for m in data.get("models", [])]
    if not any("llama3.1:8b" in name for name in model_names):
        logger.error("llama3.1:8b が見つかりません。利用可能なモデル: %s", model_names)
        logger.error("'ollama pull llama3.1:8b' を実行してからやり直してください")
        sys.exit(1)

    logger.info("Ollama 接続確認 OK: llama3.1:8b 利用可能")


def _load_env() -> dict[str, str]:
    """config/.env を読み込んで環境変数辞書を返す"""
    env = os.environ.copy()
    if ENV_PATH.exists():
        try:
            for line in ENV_PATH.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
        except OSError as e:
            logger.warning(".env 読み込みエラー（スキップして続行）: %s", e)
    return env


def make_transport() -> StdioTransport:
    """Cognee MCPサーバー接続用のStdioTransportを作成"""
    return StdioTransport(
        command=str(PROJECT_ROOT / "src" / "venv" / "bin" / "python3"),
        args=[MCP_COMMAND],
        env=_load_env(),
    )


async def import_one(client: Client, file_path: Path, idx: int, total: int) -> bool:
    """1ファイルを投入。成功時 True、失敗時 False を返す"""
    rel = file_path.relative_to(INPUT_DIR)
    content = file_path.read_text(encoding="utf-8")

    for attempt in range(1, MAX_RETRY + 1):
        try:
            result = await client.call_tool("remember", {
                "data": content,
                "dataset_name": DATASET_NAME,
            })
            text = result.content[0].text if result and result.content else ""

            if "status=completed" in text:
                logger.info("[%d/%d] ✓ %s (試行%d)", idx, total, rel, attempt)
                return True

            if "status=errored" in text:
                logger.warning("[%d/%d] ✗ %s (試行%d/%d): errored", idx, total, rel, attempt, MAX_RETRY)
                if attempt < MAX_RETRY:
                    await asyncio.sleep(2)
                    continue
                return False

            # 想定外のステータス
            logger.warning("[%d/%d] 想定外の応答: %s", idx, total, text[:120])
            return False
        except Exception as e:
            logger.warning("[%d/%d] 例外発生（試行%d/%d）: %s", idx, total, attempt, MAX_RETRY, e)
            if attempt < MAX_RETRY:
                await asyncio.sleep(2)
                continue
            return False

    return False


async def import_all(files: list[Path], dry_run: bool) -> tuple[int, int]:
    """全ファイルを投入。 (成功件数, 失敗件数) を返す"""
    success = 0
    failed = 0
    total = len(files)

    if dry_run:
        for idx, f in enumerate(files, 1):
            rel = f.relative_to(INPUT_DIR)
            logger.info("[%d/%d] (dry-run) %s", idx, total, rel)
        return total, 0

    async with Client(make_transport()) as client:
        for idx, f in enumerate(files, 1):
            ok = await import_one(client, f, idx, total)
            if ok:
                success += 1
            else:
                failed += 1
                logger.error("失敗3回・全停止: %s", f.relative_to(INPUT_DIR))
                logger.error("失敗を見過ごさないため処理を停止します。原因確認後に再実行してください。")
                break

    return success, failed


def main() -> None:
    """エントリーポイント"""
    parser = argparse.ArgumentParser(description="user_chunks/をCogneeに投入")
    parser.add_argument("--dry-run", action="store_true", help="ファイル一覧を表示するだけ（投入しない）")
    args = parser.parse_args()

    if not INPUT_DIR.exists():
        logger.error("入力フォルダが見つかりません: %s", INPUT_DIR)
        logger.error("先に split_knowledge.py を実行してください")
        sys.exit(1)

    md_files = sorted(INPUT_DIR.glob("**/*.md"))
    # README.md は投入対象外
    md_files = [f for f in md_files if f.name != "README.md"]

    if not md_files:
        logger.warning("投入対象の .md ファイルが見つかりません: %s", INPUT_DIR)
        logger.warning("先に split_knowledge.py を実行してください")
        sys.exit(1)

    if not args.dry_run:
        check_ollama()

    logger.info("投入対象: %d 件 → dataset=%s", len(md_files), DATASET_NAME)
    success, failed = asyncio.run(import_all(md_files, args.dry_run))

    logger.info("=" * 50)
    logger.info("成功: %d 件", success)
    logger.info("失敗: %d 件", failed)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
