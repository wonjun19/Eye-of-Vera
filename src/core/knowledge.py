import os
import shutil

from config.user_config import KNOWLEDGE_DIR
from src.utils.logger import get_logger

logger = get_logger(__name__)


def _parse_frontmatter(content: str) -> tuple[dict, str]:
    """간단한 YAML 프론트매터를 파싱한다."""
    if not content.startswith("---"):
        return {}, content
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}, content
    meta = {}
    for line in parts[1].strip().splitlines():
        if ":" in line:
            key, val = line.split(":", 1)
            meta[key.strip()] = val.strip()
    return meta, parts[2].strip()


def ensure_knowledge_dir():
    os.makedirs(KNOWLEDGE_DIR, exist_ok=True)


def load_knowledge_files() -> list[dict]:
    """knowledge/ 폴더의 모든 지식 파일을 로드한다."""
    ensure_knowledge_dir()
    files = []
    for name in sorted(os.listdir(KNOWLEDGE_DIR)):
        if not name.endswith((".md", ".txt")):
            continue
        path = os.path.join(KNOWLEDGE_DIR, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError:
            continue
        meta, body = _parse_frontmatter(content)
        tags = [t.strip() for t in meta.get("tags", "").split(",") if t.strip()]
        files.append({
            "name": name,
            "path": path,
            "tags": tags,
            "body": body,
        })
    return files


def add_knowledge_file(src_path: str) -> str | None:
    """외부 파일을 knowledge/ 폴더로 복사한다. 복사된 파일 이름을 반환."""
    ensure_knowledge_dir()
    name = os.path.basename(src_path)
    dest = os.path.join(KNOWLEDGE_DIR, name)
    if os.path.exists(dest):
        base, ext = os.path.splitext(name)
        i = 1
        while os.path.exists(dest):
            name = f"{base}_{i}{ext}"
            dest = os.path.join(KNOWLEDGE_DIR, name)
            i += 1
    try:
        shutil.copy2(src_path, dest)
        # 프론트매터가 없으면 빈 태그로 추가
        with open(dest, "r", encoding="utf-8") as f:
            content = f.read()
        if not content.startswith("---"):
            with open(dest, "w", encoding="utf-8") as f:
                f.write(f"---\ntags: \n---\n\n{content}")
        return name
    except OSError as e:
        logger.error("지식 파일 복사 실패: %s", e)
        return None


def delete_knowledge_file(name: str) -> bool:
    path = os.path.join(KNOWLEDGE_DIR, name)
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def update_tags(name: str, new_tags: list[str]):
    """파일의 프론트매터 태그를 업데이트한다."""
    path = os.path.join(KNOWLEDGE_DIR, name)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    _, body = _parse_frontmatter(content)
    tag_str = ", ".join(new_tags)
    new_content = f"---\ntags: {tag_str}\n---\n\n{body}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)


def find_relevant_knowledge(user_message: str, enabled_files: list[str]) -> str:
    """사용자 메시지와 관련된 지식을 검색하여 컨텍스트 문자열로 반환한다."""
    all_files = load_knowledge_files()
    if not all_files:
        return ""

    msg_lower = user_message.lower()
    enabled = [f for f in all_files if f["name"] in enabled_files]
    if not enabled:
        return ""

    # 태그 매칭으로 관련 파일 필터링
    matched = [f for f in enabled if any(t.lower() in msg_lower for t in f["tags"])]

    # 매칭 없으면 활성화된 전체 파일 사용
    if not matched:
        matched = enabled

    # 최대 3개 파일, 파일당 500자 제한
    matched = matched[:3]
    lines = ["### 참고 지식"]
    for f in matched:
        lines.append(f"\n#### {f['name']}")
        body = f["body"][:500]
        if len(f["body"]) > 500:
            body += "..."
        lines.append(body)

    return "\n".join(lines)
