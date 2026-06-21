"""IR-stage wiki lookup. Queries the INGESTED llm-wiki (conflict-resolved
entities/concepts + conflicts.md) — NOT the raw Spec catalog. This ensures the
IR enrichment step sees CustomerReq>Spec / UserPrompt>ModelDefault overrides."""
import re
from pathlib import Path
from ir_generator.config import Config

EXCERPT_CHARS = 1200
_FM = re.compile(r'^---\n(.*?)\n---\n?(.*)$', re.DOTALL)


def _frontmatter(content: str) -> tuple[str, str]:
    m = _FM.match(content)
    return (m.group(1), m.group(2)) if m else ("", content)


def _title_tags(content: str, fallback: str) -> tuple[str, list[str]]:
    fm, body = _frontmatter(content)
    tm = re.search(r'^title:\s*"?(.+?)"?\s*$', fm, re.MULTILINE)
    title = tm.group(1).strip() if tm else None
    if not title:
        hm = re.search(r'^#\s+(.+)$', body, re.MULTILINE)
        title = hm.group(1).strip() if hm else fallback
    tg = re.search(r'^tags:\s*\[(.+?)\]', fm, re.MULTILINE)
    tags = [t.strip().strip('"\'') for t in tg.group(1).split(",")] if tg else []
    return title, tags


def extract_commands(phase: dict) -> list[str]:
    """Terms from a phase's SCSI/UFS commands + IDN entity names (e.g. bBootLunEn)."""
    terms = []
    for step in phase.get("steps", []):
        for field in ("scsi_cmd", "ufs_query"):
            val = step.get(field)
            if val:
                terms.extend(w for w in re.sub(r'[()（）]', ' ', val).lower().split()
                             if len(w) > 2)
        idn = step.get("idn") or ""
        if idn:
            terms.extend(w for w in re.sub(r'[()（）]', ' ', idn).lower().split()
                         if len(w) > 2)
    return list(set(terms))


def _ingested_pages(wiki_path: Path) -> list[dict]:
    pages = []
    for sub in ("entities", "concepts"):
        d = wiki_path / sub
        if not d.exists():
            continue
        for p in sorted(d.glob("*.md")):
            content = p.read_text(encoding="utf-8", errors="ignore")
            title, tags = _title_tags(content, p.stem)
            pages.append({"file": f"{sub}/{p.name}", "stem": p.stem,
                          "title": title, "tags": tags, "content": content})
    return pages


def _page_matches(page: dict, terms: list[str]) -> bool:
    meta = f"{page['title'].lower()} {' '.join(page['tags']).lower()} {page['stem'].lower()}"
    if any(t in meta for t in terms):
        return True
    # content match only for specific (long) terms, to avoid generic words matching all
    low = page["content"].lower()
    return any(len(t) >= 5 and t in low for t in terms)


def load_conflicts(wiki_path: Path) -> dict | None:
    p = wiki_path / "conflicts.md"
    if not p.exists():
        return None
    return {
        "title": "Conflict-Resolved Overrides (CustomerReq>Spec, UserPrompt>ModelDefault)",
        "file": "conflicts.md",
        "excerpt": p.read_text(encoding="utf-8", errors="ignore")[:EXCERPT_CHARS],
    }


def lookup_wiki(skeleton: dict, config: Config) -> dict[str, list[dict]]:
    """Per-phase ingested-wiki refs. Always includes a global '__conflicts__'
    entry carrying the conflict-resolved overrides (highest authority)."""
    pages = _ingested_pages(config.wiki_path)
    refs: dict[str, list[dict]] = {}

    for phase in skeleton.get("phases", []):
        pid = phase["phase_id"]
        terms = extract_commands(phase)
        matched, seen = [], set()
        for page in pages:
            if page["file"] in seen:
                continue
            if _page_matches(page, terms):
                matched.append({"title": page["title"], "file": page["file"],
                                "excerpt": page["content"][:EXCERPT_CHARS]})
                seen.add(page["file"])
        refs[pid] = matched

    conflicts = load_conflicts(config.wiki_path)
    if conflicts:
        refs["__conflicts__"] = [conflicts]

    return refs
