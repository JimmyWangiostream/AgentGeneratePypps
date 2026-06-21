#!/usr/bin/env python3
"""Query the understand-anything knowledge graph.

This is the CODE-grounding mechanism for pattern generation. It uses the
structural graph built by understand-anything (.understand-anything/
knowledge-graph.json) — NOT a text search — to look up a symbol, get its real
file:line location and call/import relationships. The generator then reads the
real source slice at that location.

CLI:
    python graph_query.py <symbol>        # find symbol, show file:lines + edges
    python graph_query.py <symbol> --src  # also print the source slice
"""
import json
import sys
from pathlib import Path
from collections import defaultdict

_REPO = Path(__file__).resolve().parent
_GRAPH = _REPO / ".understand-anything" / "knowledge-graph.json"


class GraphQuery:
    def __init__(self, graph_path=None, repo_root=None):
        self.repo_root = Path(repo_root) if repo_root else _REPO
        g = json.loads(Path(graph_path or _GRAPH).read_text(encoding="utf-8"))
        self.nodes = {n["id"]: n for n in g["nodes"]}
        self._by_name = defaultdict(list)
        for n in g["nodes"]:
            if n.get("name"):
                self._by_name[n["name"].lower()].append(n)
        self._callees = defaultdict(list)
        self._callers = defaultdict(list)
        self._imports = defaultdict(list)
        for e in g["edges"]:
            if e["type"] == "calls":
                self._callees[e["source"]].append(e["target"])
                self._callers[e["target"]].append(e["source"])
            elif e["type"] == "imports":
                self._imports[e["source"]].append(e["target"])

    def find(self, name: str) -> list[dict]:
        """Exact name match first, else substring. Returns graph nodes."""
        nl = name.lower()
        exact = self._by_name.get(nl, [])
        if exact:
            return exact
        return [n for n in self.nodes.values()
                if n.get("name") and nl in n["name"].lower()]

    def callees(self, node_id: str) -> list[str]:
        return [self.nodes[t]["name"] for t in self._callees.get(node_id, [])
                if t in self.nodes]

    def callers(self, node_id: str) -> list[str]:
        return [self.nodes[s]["name"] for s in self._callers.get(node_id, [])
                if s in self.nodes]

    def source_slice(self, node: dict) -> str:
        fp = node.get("filePath")
        if not fp:
            return ""
        p = self.repo_root / fp
        if not p.exists():
            return ""
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        start = max((node.get("startLine") or 1) - 1, 0)
        end = node.get("endLine") or len(lines)
        return "\n".join(lines[start:end])


def main():
    if len(sys.argv) < 2:
        print("Usage: python graph_query.py <symbol> [--src]")
        sys.exit(0)
    name = sys.argv[1]
    show_src = "--src" in sys.argv[2:]
    gq = GraphQuery()
    hits = gq.find(name)
    if not hits:
        print(f"[NO MATCH] '{name}' not found in knowledge graph")
        return
    print(f"[GRAPH] {len(hits)} match(es) for '{name}':\n")
    for n in hits[:10]:
        loc = f"{n.get('filePath')}:{n.get('startLine')}-{n.get('endLine')}"
        print(f"  {n.get('type'):9} {n.get('name')}  @ {loc}")
        cl = gq.callees(n["id"])
        if cl:
            print(f"      calls: {', '.join(cl[:8])}")
        if show_src:
            print("      ----")
            for ln in gq.source_slice(n).splitlines()[:25]:
                print(f"      {ln}")
            print()


if __name__ == "__main__":
    main()
