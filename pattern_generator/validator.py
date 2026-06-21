"""Validate a generated pattern: syntax, structural fidelity to the IR, and that
imported names exist in the code graph. No LLM."""
import ast


def validate(py_source: str, ir: dict, code_retriever=None) -> dict:
    """Validate syntax, IR structural fidelity, and (optionally) imported names.

    code_retriever: any object with find_by_name(name) -> list, or None.
    When None, the import check is skipped and imports are reported as 'pass'.
    """
    result = {"syntax": "pass", "structure": "pass", "imports": "pass"}

    try:
        tree = ast.parse(py_source)
    except SyntaxError as e:
        result["syntax"] = f"SyntaxError: {e}"
        return result  # can't go further without a parse

    # Structure: every count-loop's loop_count literal must appear in source
    struct_issues = []
    for phase in ir.get("phases", []):
        if phase.get("type") == "loop" and phase.get("loop_type") == "count":
            lc = phase.get("loop_count")
            if lc is not None and str(lc) not in py_source:
                struct_issues.append(f"{phase['phase_id']}: loop_count {lc} not found")
    if struct_issues:
        result["structure"] = struct_issues

    # Imports: skip when no code_retriever is provided
    if code_retriever is not None:
        import_issues = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    if alias.name != "*" and not code_retriever.find_by_name(alias.name):
                        import_issues.append(f"{node.module}.{alias.name}")
        if import_issues:
            result["imports"] = import_issues

    return result
