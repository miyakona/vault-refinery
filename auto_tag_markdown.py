import os
import re
import yaml
from keybert import KeyBERT
from sudachipy import tokenizer, dictionary
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import anthropic
from dotenv import load_dotenv
import glob
from datetime import datetime
import sys
import unicodedata

LOG_DIR = "logs"
RUN_TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_ERROR_FILE = os.path.join(LOG_DIR, f"auto_tag_errors_{RUN_TIMESTAMP}.log")
LOG_INFO_FILE = os.path.join(LOG_DIR, f"auto_tag_info_{RUN_TIMESTAMP}.log")

def log_error(md_path, error):
    os.makedirs(LOG_DIR, exist_ok=True)
    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    with open(LOG_ERROR_FILE, "a", encoding="utf-8") as f:
        f.write(f"{now}\t{md_path}\t{error}\n")

def log_info(message):
    os.makedirs(LOG_DIR, exist_ok=True)
    now = datetime.now().isoformat(sep=' ', timespec='seconds')
    with open(LOG_INFO_FILE, "a", encoding="utf-8") as f:
        f.write(f"{now}\t{message}\n")

# frontmatter抽出
def extract_frontmatter(md_text):
    m = re.match(r"^---\n(.*?)\n---\n(.*)", md_text, re.DOTALL)
    if m:
        try:
            frontmatter_clean = remove_control_chars(m.group(1))
            meta = yaml.safe_load(frontmatter_clean)
            if not isinstance(meta, dict):
                meta = {}
        except Exception as e:
            log_error("<frontmatter>", f"YAML parse error: {e}")
            meta = {}
        return meta, m.group(2)
    return {}, md_text

# frontmatter再構築
def build_frontmatter(meta, body):
    return f"---\n{yaml.safe_dump(meta, allow_unicode=True)}---\n{body}"

def tag_md_claude(text):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY環境変数が設定されていません")
    client = anthropic.Anthropic(api_key=api_key)
    model_name = "claude-3-5-haiku-20241022"
    prompt = f"""
以下のMarkdown本文の内容に最も関連するタグを最大10個ずつ、日本語と英語でそれぞれ作成してください。
出力は以下のフォーマットで、タグだけを出力してください。

日本語タグ: （意味のある単語や短いフレーズのみ。1文字や意味不明なものは禁止。例: プライバシー, 仮想通貨, 技術倫理, 法律）
英語タグ: （意味のある単語や短いフレーズのみ。例: privacy, cryptocurrency, ethics, law）

例:
日本語タグ: プライバシー, 仮想通貨, 技術倫理, 法律
英語タグ: privacy, cryptocurrency, ethics, law

本文:
{text}
"""
    message = client.messages.create(
        model=model_name,
        max_tokens=256,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()

def extract_tags_from_claude_output(output):
    jp = re.search(r"日本語タグ[:：]\s*(.+)", output)
    en = re.search(r"英語タグ[:：]\s*(.+)", output)
    jp_tags = [t.strip() for t in jp.group(1).split(",")] if jp else []
    en_tags = [t.strip() for t in en.group(1).split(",")] if en else []
    return jp_tags[:10] + en_tags[:10]

# 制御文字除去関数
def remove_control_chars(s):
    return ''.join(c for c in s if unicodedata.category(c)[0] != 'C' or c in '\n\t')

def get_tags_from_frontmatter(md_path):
    with open(md_path, encoding="utf-8") as f:
        lines = []
        in_frontmatter = False
        for line in f:
            if line.strip() == "---":
                if in_frontmatter:
                    break
                else:
                    in_frontmatter = True
                    continue
            if in_frontmatter:
                lines.append(line)
        if lines:
            try:
                meta = yaml.safe_load("".join(lines))
                if not isinstance(meta, dict):
                    return set()
                return set(meta.get("tags", []) or [])
            except Exception as e:
                log_error(md_path, f"YAML parse error: {e}")
                return set()
    return set()

# タグ付け本体
def auto_tag_markdown(md_path):
    if "タグなし" in md_path:
        log_info(f"Skip: {md_path} (in タグなし dir)")
        return
    existing_tags = get_tags_from_frontmatter(md_path)
    if any(tag.lower() != "clippings" for tag in existing_tags if tag.strip()):
        log_info(f"Skip: {md_path} (already tagged)")
        return
    with open(md_path, encoding="utf-8") as f:
        md_text = f.read()
    md_text = remove_control_chars(md_text)
    meta, body = extract_frontmatter(md_text)
    if not body.strip():
        title = os.path.splitext(os.path.basename(md_path))[0]
        tag_input = title
    else:
        tag_input = body
    tags_str = tag_md_claude(tag_input)
    tags = extract_tags_from_claude_output(tags_str)
    old_tags = set(meta.get("tags", []) or [])
    meta["tags"] = sorted(list(old_tags | set(tags)))[:20]
    new_md = build_frontmatter(meta, body)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(new_md)
    log_info(f"Tagged: {md_path} -> {meta['tags']}")

def process_all_md_files(root_dir):
    md_files = glob.glob(os.path.join(root_dir, "**", "*.md"), recursive=True)
    for md_path in md_files:
        try:
            auto_tag_markdown(md_path)
        except Exception as e:
            print(f"Error tagging {md_path}: {e}")
            log_error(md_path, e)

if __name__ == "__main__":
    load_dotenv()
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if os.path.isfile(arg):
                try:
                    auto_tag_markdown(arg)
                except Exception as e:
                    print(f"Error tagging {arg}: {e}")
                    log_error(arg, e)
            else:
                print(f"File not found: {arg}")
    else:
        process_all_md_files("/Users/miyakona/Obsidian Vault/") 