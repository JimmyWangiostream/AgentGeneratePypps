import re
from pathlib import Path
from typing import Optional

# Expected values with these patterns get a fail_condition
_CONDITION_RE = re.compile(
    r'!=|==\s*0x|Data Match|bPurge|!=\s*0x', re.IGNORECASE
)

# Phase / loop header patterns
_PHASE_RE = re.compile(r'^## Phase ([0-9A-Za-z]+)\s*[—\-]+\s*(.+)', re.MULTILINE)
_LOOP_RE  = re.compile(r'^## Loop\s*[—\-]+\s*(.+)', re.MULTILINE)

# Loop count in header e.g. "(100 次)"
_LOOP_COUNT_RE = re.compile(r'\((\d+)\s*次\)')

# Step header: ### or #### Step X.Y: Name
_STEP_SPLIT_RE = re.compile(
    r'^(#{3,4} Step ([\w.]+):\s*(.+))$', re.MULTILINE
)

# Within a step block
_SCSI_RE      = re.compile(r'\*\*SCSI CMD\*\*[：:]\s*`?([^`\n]+)`?')
_QUERY_RE     = re.compile(r'\*\*UFS QUERY\*\*[：:]\s*`?([^`\n]+)`?')
_EXPECTED_RE  = re.compile(r'\*\*Expected\*\*[：:]\s*(.+)')
_OPCODE_RE    = re.compile(r'\|\s*Opcode\s*\|\s*([^|\n]+)\|')
_QOPCODE_RE   = re.compile(r'\|\s*Query Opcode\s*\|\s*([^|\n]+)\|')
_IDN_RE       = re.compile(r'\|\s*IDN\s*\|\s*([^|\n]+)\|')

# Sections to skip (not phases)
_SKIP_HEADERS = {"測試目標", "JIRA", "測試架構", "附錄", "自我驗證"}


def _parse_frontmatter(text: str) -> dict:
    m = re.match(r'^---\n(.*?)\n---', text, re.DOTALL)
    if not m:
        return {}
    fm = m.group(1)

    title_m = re.search(r'^title:\s*(.+)', fm, re.MULTILINE)
    desc_m  = re.search(r'^description:\s*>\n\s+(.+)', fm, re.MULTILINE)
    tags_m  = re.search(r'^tags:\s*\[(.+?)\]', fm, re.MULTILINE)

    return {
        "title": title_m.group(1).strip() if title_m else "",
        "description": desc_m.group(1).strip() if desc_m else "",
        "tags": [t.strip().strip("'\"") for t in tags_m.group(1).split(",")] if tags_m else [],
    }


def _extract_pattern_id(title: str) -> str:
    m = re.match(r'(PF\d+_\d+)', title, re.IGNORECASE)
    return m.group(1).upper() if m else title.split()[0]


def _parse_step_block(step_id: str, name: str, block: str) -> dict:
    scsi     = _SCSI_RE.search(block)
    query    = _QUERY_RE.search(block)
    expected = _EXPECTED_RE.search(block)
    opcode   = _OPCODE_RE.search(block)
    qopcode  = _QOPCODE_RE.search(block)
    idn      = _IDN_RE.search(block)

    exp_text = expected.group(1).strip().rstrip("。.") if expected else ""
    has_cond = bool(_CONDITION_RE.search(exp_text))

    return {
        "step_id":      "step_" + step_id.replace(".", "_"),
        "name":         name.strip(),
        "scsi_cmd":     scsi.group(1).strip() if scsi else None,
        "ufs_query":    query.group(1).strip() if query else None,
        "opcode":       opcode.group(1).strip() if opcode else None,
        "query_opcode": qopcode.group(1).strip() if qopcode else None,
        "idn":          idn.group(1).strip() if idn else None,
        "expected":     exp_text,
        "fail_condition": f"NOT ({exp_text})" if has_cond else None,
        "on_fail":      "abort" if has_cond else None,
        "raw_content":  block.strip(),
    }


def _split_steps(content: str) -> list[tuple[str, str, str]]:
    """Split content into (step_id, step_name, block) tuples."""
    parts = _STEP_SPLIT_RE.split(content)
    # parts layout: [pre, full_hdr, step_id, step_name, body, full_hdr, ...]
    results = []
    i = 1
    while i + 3 < len(parts):
        step_id   = parts[i + 1]
        step_name = parts[i + 2]
        body      = parts[i + 3]
        results.append((step_id, step_name.strip(), body))
        i += 4
    return results


def _split_phase_blocks(text: str) -> list[tuple[str, str]]:
    """Return (header_line, content) for each ## section."""
    parts = re.split(r'^(## .+)$', text, flags=re.MULTILINE)
    blocks = []
    for i in range(1, len(parts), 2):
        content = parts[i + 1] if i + 1 < len(parts) else ""
        blocks.append((parts[i], content))
    return blocks


def _parse_phase(header: str, content: str, phase_index: int) -> Optional[dict]:
    if any(s in header for s in _SKIP_HEADERS):
        return None

    phase_m = _PHASE_RE.match(header)
    loop_m  = _LOOP_RE.match(header)

    if phase_m:
        phase_id   = f"phase_{phase_m.group(1)}"
        name       = phase_m.group(2).strip()
        phase_type = "sequential"
        loop_type  = loop_count = loop_condition = None
    elif loop_m:
        name       = loop_m.group(1).strip()
        phase_id   = f"loop_{phase_index}"
        phase_type = "loop"
        count_m    = _LOOP_COUNT_RE.search(name)
        loop_type  = "count" if count_m else "condition"
        loop_count = int(count_m.group(1)) if count_m else None
        loop_condition = None
    else:
        return None

    steps = [
        _parse_step_block(sid, sname, sblock)
        for sid, sname, sblock in _split_steps(content)
    ]

    return {
        "phase_id":       phase_id,
        "name":           name,
        "type":           phase_type,
        "loop_type":      loop_type,
        "loop_count":     loop_count,
        "loop_condition": loop_condition,
        "steps":          steps,
    }


def parse_tc(path: Path) -> dict:
    text = Path(path).read_text(encoding="utf-8")
    fm   = _parse_frontmatter(text)

    pattern_id = _extract_pattern_id(fm.get("title", ""))

    phases = []
    for i, (header, content) in enumerate(_split_phase_blocks(text)):
        phase = _parse_phase(header, content, i)
        if phase and phase["steps"]:
            phases.append(phase)

    return {
        "pattern_id":  pattern_id,
        "title":       fm.get("title", ""),
        "description": fm.get("description", ""),
        "tags":        fm.get("tags", []),
        "phases":      phases,
    }
