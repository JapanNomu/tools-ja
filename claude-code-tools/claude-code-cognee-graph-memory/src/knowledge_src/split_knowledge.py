"""
ノウハウファイル（.md）をH2見出しごとに分割する。

Cogneeのcognify処理は大きいファイル（数百行）でLLMが要約失敗することがあるため、
H2（## 見出し）ごとに小さく分割してから投入する。各分割ファイルには元ファイルへの
参照情報を冒頭に付与する。

使用方法:
    cd <配布用のルートディレクトリ>
    src/venv/bin/python3 src/knowledge_src/split_knowledge.py

入力:  knowledge/user_knowledge/  配下の .md ファイル
出力:  knowledge/user_chunks/     配下の分割ファイル群
"""
import logging
import re
import shutil
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INPUT_DIR = PROJECT_ROOT / "knowledge" / "user_knowledge"
OUTPUT_DIR = PROJECT_ROOT / "knowledge" / "user_chunks"


def sanitize_filename(name: str) -> str:
    """ファイル名に使えない文字を除去・置換"""
    name = re.sub(r"[/\\:*?\"<>|]", "", name)
    name = re.sub(r"\s+", "_", name.strip())
    if len(name) > 60:
        name = name[:60]
    return name


def split_md_by_h2(content: str) -> tuple[list[tuple[str, str]], str]:
    """マークダウンをH2見出しで分割。

    Returns:
        (sections, h1_title)
        sections: [(セクション名, セクション本文), ...]
        h1_title: H1見出しテキスト（無ければ空）
    """
    lines = content.split("\n")
    sections: list[tuple[str, str]] = []

    h1_title = ""
    i = 0
    # H1 と H2 より前の前文をスキップ
    while i < len(lines):
        line = lines[i]
        if line.startswith("# "):
            h1_title = line[2:].strip()
            i += 1
            continue
        if line.startswith("## "):
            break
        i += 1

    # H2 見出しごとに分割
    current_section_title = ""
    current_lines: list[str] = []

    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            if current_section_title:
                sections.append((current_section_title, "\n".join(current_lines).strip()))
            current_section_title = line[3:].strip()
            current_lines = [line]
        else:
            current_lines.append(line)
        i += 1

    if current_section_title:
        sections.append((current_section_title, "\n".join(current_lines).strip()))

    return sections, h1_title


def process_file(md_path: Path) -> int:
    """1ファイルを分割して user_chunks/ に出力。生成chunk数を返す"""
    rel = md_path.relative_to(INPUT_DIR)
    content = md_path.read_text(encoding="utf-8")
    sections, h1_title = split_md_by_h2(content)

    out_dir = OUTPUT_DIR / rel.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    # H2 が無いファイルはそのまま1chunkとして出す
    if not sections:
        out_path = out_dir / (md_path.stem + "_00_全文.md")
        out_path.write_text(content, encoding="utf-8")
        return 1

    base_name = md_path.stem
    chunk_count = 0
    for idx, (section_title, section_body) in enumerate(sections, 1):
        # 元ファイルへの参照メタ情報をchunk冒頭に付与
        header = (
            f"# {h1_title} - {section_title}\n\n"
            f"> このファイルは `user_knowledge/{rel}` の章 `{section_title}` を分割したものです。\n"
            f"> 元ドキュメント全体: `user_knowledge/{rel}`\n\n"
        )
        chunk_content = header + section_body

        section_clean = sanitize_filename(section_title)
        chunk_filename = f"{base_name}_{idx:02d}_{section_clean}.md"
        out_path = out_dir / chunk_filename
        out_path.write_text(chunk_content, encoding="utf-8")
        chunk_count += 1

    return chunk_count


def main() -> None:
    """エントリーポイント"""
    if not INPUT_DIR.exists():
        logger.error("入力フォルダが見つかりません: %s", INPUT_DIR)
        sys.exit(1)

    md_files = sorted(INPUT_DIR.glob("**/*.md"))
    # README.md は分割対象外（フォルダの説明書なので投入しない）
    md_files = [f for f in md_files if f.name != "README.md"]

    if not md_files:
        logger.warning("分割対象の .md ファイルが見つかりません: %s", INPUT_DIR)
        logger.warning("user_knowledge/ にノウハウファイルを配置してから再実行してください")
        sys.exit(1)

    # 既存のchunksをクリアしてから再生成
    if OUTPUT_DIR.exists():
        # README.md は残す
        for item in OUTPUT_DIR.iterdir():
            if item.name == "README.md":
                continue
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
        logger.info("既存のchunksをクリア: %s", OUTPUT_DIR)
    else:
        OUTPUT_DIR.mkdir(parents=True)

    logger.info("分割対象: %d ファイル", len(md_files))
    total_chunks = 0
    for md_path in md_files:
        rel = md_path.relative_to(INPUT_DIR)
        n = process_file(md_path)
        total_chunks += n
        logger.info("  %s: %d chunks", rel, n)

    logger.info("分割完了: 合計 %d chunks 生成", total_chunks)
    logger.info("出力先: %s", OUTPUT_DIR)


if __name__ == "__main__":
    main()
