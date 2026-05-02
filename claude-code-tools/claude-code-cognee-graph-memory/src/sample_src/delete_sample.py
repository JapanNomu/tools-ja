"""
sample_knowledge データセットを Cognee グラフ記憶から削除する。

サンプルで動作確認が済んだ後、自分のノウハウだけでクリーンに使い始めたい時に使う。
他のデータセット（user_knowledge等）には影響しない。

使用方法:
    cd <配布用のルートディレクトリ>
    src/venv/bin/python3 src/sample_src/delete_sample.py
"""
import asyncio
import logging
import os
import sys
from pathlib import Path

from fastmcp import Client
from fastmcp.client.transports import StdioTransport

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# このファイルから配布用のルートを解決する
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
ENV_PATH = PROJECT_ROOT / "config" / ".env"
MCP_COMMAND = str(PROJECT_ROOT / "src" / "main_src" / "start_cognee_mcp.py")
DATASET_NAME = "sample_knowledge"


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


async def delete_sample_dataset() -> None:
    """sample_knowledge データセットを削除する"""
    logger.info("削除対象データセット: %s", DATASET_NAME)
    async with Client(make_transport()) as client:
        try:
            result = await client.call_tool("delete_dataset", {
                "dataset_name": DATASET_NAME,
            })
            text = result.content[0].text if result and result.content else ""
            logger.info("削除結果: %s", text)
        except Exception as e:
            logger.error("削除失敗: %s", e)
            sys.exit(1)


def main() -> None:
    """エントリーポイント"""
    asyncio.run(delete_sample_dataset())


if __name__ == "__main__":
    main()
