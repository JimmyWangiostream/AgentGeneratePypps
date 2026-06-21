#!/usr/bin/env python3
"""
Query the integrated UFS Pattern Wiki
"""

import re
from pathlib import Path
from typing import List, Dict, Tuple

_REPO_ROOT = Path(__file__).resolve().parent
_DEFAULT_WIKI = _REPO_ROOT / "wiki"


def _split_frontmatter(content: str) -> Tuple[str, str]:
    """Return (frontmatter, body). Strips a leading YAML --- ... --- block."""
    if content.startswith("---"):
        m = re.match(r"^---\n(.*?)\n---\n?(.*)$", content, re.DOTALL)
        if m:
            return m.group(1), m.group(2)
    return "", content


def _extract_title(content: str, fallback: str) -> str:
    """Title from frontmatter `title:`, else first markdown heading, else fallback."""
    fm, body = _split_frontmatter(content)
    tm = re.search(r'^title:\s*"?(.+?)"?\s*$', fm, re.MULTILINE)
    if tm:
        return tm.group(1).strip()
    hm = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
    if hm:
        return hm.group(1).strip()
    return fallback


def _extract_snippet(content: str, query_terms: List[str]) -> Tuple[str, List[str]]:
    """Return (lead_paragraph, matched_lines).

    lead_paragraph: first prose line after the title (skips headings/tables/rules).
    matched_lines: non-heading lines (e.g. table rows) containing a query term.
    """
    _, body = _split_frontmatter(content)
    lines = body.split("\n")

    lead = ""
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#") or s.startswith("|") or s.startswith("---"):
            continue
        lead = s
        break

    matched: List[str] = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        low = s.lower()
        if any(t in low for t in query_terms):
            matched.append(s)
        if len(matched) >= 5:
            break

    return lead, matched


class WikiQuery:
    """Query the wiki for information"""

    def __init__(self, wiki_root: str | Path | None = None):
        self.wiki_root = Path(wiki_root) if wiki_root else _DEFAULT_WIKI
        self.entities_dir = self.wiki_root / "entities"
        self.sources_dir = self.wiki_root / "sources"

    def search_entities(self, query: str) -> List[Dict]:
        """Search entity pages for matching content."""
        results = []
        query_terms = [t for t in query.lower().split() if t]
        if not query_terms:
            return results

        for entity_file in sorted(self.entities_dir.glob("*.md")):
            try:
                content = entity_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            low = content.lower()
            score = sum(low.count(t) for t in query_terms)
            if score <= 0:
                continue

            title = _extract_title(content, entity_file.stem)
            lead, matched = _extract_snippet(content, query_terms)
            definition = (lead or (matched[0] if matched else ""))[:300]

            results.append({
                "title": title,
                "file": entity_file.name,
                "definition": definition,
                "matched_lines": matched,
                "match_score": score,
            })

        return sorted(results, key=lambda x: x["match_score"], reverse=True)

    def search_sources(self, query: str) -> List[Dict]:
        """Search source summary pages."""
        results = []
        query_lower = query.lower()

        for source_file in sorted(self.sources_dir.glob("*.md")):
            try:
                content = source_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue

            if query_lower in content.lower():
                title = _extract_title(content, source_file.stem)
                matching_lines = [
                    l.strip() for l in content.split("\n")
                    if query_lower in l.lower() and l.strip() and not l.strip().startswith("#")
                ][:3]
                results.append({
                    "source": source_file.name.replace(".md", ""),
                    "title": title,
                    "matches": matching_lines,
                })

        return results

    def query(self, question: str) -> str:
        """Query the wiki and return formatted results."""
        print()
        print("=" * 70)
        print(f"Wiki Query: {question}")
        print("=" * 70)
        print()

        entity_results = self.search_entities(question)

        if entity_results:
            print("[ENTITIES] Related Entities Found:")
            print()
            for i, result in enumerate(entity_results[:5], 1):
                print(f"{i}. {result['title']}  (score={result['match_score']})")
                if result["definition"]:
                    print(f"   {result['definition'][:120]}")
                for ln in result.get("matched_lines", [])[:3]:
                    print(f"   | {ln[:120]}")
                print()
        else:
            print("[NO MATCH] No matching entities found")
            print()

        source_results = self.search_sources(question)

        if source_results:
            print("[SOURCES] Relevant Source Information:")
            print()
            for result in source_results:
                print(f"[{result['source'].upper()}] {result['title']}")
                for match in result["matches"]:
                    print(f"  - {match}")
                print()

        if entity_results or source_results:
            print("=" * 70)
            print(f"[OK] Found {len(entity_results)} entity pages and {len(source_results)} source references")
            print("=" * 70)
        else:
            print("[FAIL] No information found in wiki")

        print()
        return f"Query complete: {len(entity_results)} entities, {len(source_results)} sources"


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python wiki_query.py <query>")
        print()
        print("Examples:")
        print("  python wiki_query.py 'bBootLunEn'")
        print("  python wiki_query.py 'PSA'")
        print("  python wiki_query.py 'Thermal'")
        sys.exit(0)

    query = " ".join(sys.argv[1:])
    wiki = WikiQuery()
    wiki.query(query)
