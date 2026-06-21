# -*- coding: utf-8 -*-
"""
pattern_feature_tool.py

A Tkinter GUI tool to:
1) Create a feature folder under FEATURES_ROOT_PATH with:
   - an empty __init__.py
   - a copy of MUTUAL_FUN_TEMPLATE_PATH renamed to mutual_fun.py
2) Create pattern files by copying from a fixed template file (PATTERN_TEMPLATE_PATH)
   to a user-selected destination, using user-provided target filenames.

Pattern filename rule (user input DOES NOT need .py):
- Base name format: PSW_F_Px_yyyy_zzzz_<anything>
  * x: single digit
  * yyyy: alphanumeric (loosen on request)
  * zzzz: 4 digits
  * <anything>: at least one character
- The program will automatically append ".py".
- If user mistakenly enters ".py", it will be stripped and added back once.

Key points:
- All comments are in English.
- All functions and methods include type hints (parameters and return types).
- Paths are hard-coded relative to this file.
- We DO NOT call ensure_dir() on a file path; for files, we ensure the parent directory.
"""

from __future__ import annotations

import os
import sys
import re
import shutil
from pathlib import Path
from typing import List, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# -----------------------------------------------------------------------------
# Path helpers and hard-coded paths (relative to this file)
# -----------------------------------------------------------------------------

def get_current_directory() -> Path:
    """Return the directory where the current script resides."""
    file_path: Path
    if "__file__" in globals():
        file_path = Path(__file__).resolve()
    else:
        # Fallback for some unusual runtime environments
        file_path = Path(sys.argv[0]).resolve()
    return file_path.parent


CURRENT_DIRECTORY: Path = get_current_directory()

# NOTE: If you actually intended "../features", replace "../pattern" accordingly.
FEATURES_ROOT_PATH: Path = (CURRENT_DIRECTORY / "../pattern").resolve()

# This is a single FILE template used for creating pattern files.
PATTERN_TEMPLATE_PATH: Path = (CURRENT_DIRECTORY / "pattern_template.py").resolve()

# This is a single FILE template that will be copied into each new feature folder as mutual_fun.py.
MUTUAL_FUN_TEMPLATE_PATH: Path = (CURRENT_DIRECTORY / "mutual_fun_template.py").resolve()


def ensure_dir(dir_path: Path) -> None:
    """Ensure a directory exists; create parents if necessary."""
    dir_path.mkdir(parents=True, exist_ok=True)


def ensure_parent_dir(file_path: Path) -> Path:
    """Ensure the parent directory of a file path exists; return the parent path."""
    parent: Path = file_path.parent
    parent.mkdir(parents=True, exist_ok=True)
    return parent


def assert_file_exists(file_path: Path, human_name: str = "file") -> None:
    """Raise a clear error if `file_path` does not exist or is not a file."""
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"The {human_name} does not exist or is not a file: {file_path}")


def assert_dir_exists(dir_path: Path, human_name: str = "directory") -> None:
    """Raise a clear error if `dir_path` does not exist or is not a directory."""
    if not dir_path.exists() or not dir_path.is_dir():
        raise FileNotFoundError(f"The {human_name} does not exist or is not a directory: {dir_path}")


# -----------------------------------------------------------------------------
# Validation rules (pattern base name WITHOUT .py)
# -----------------------------------------------------------------------------

FOLDER_NAME_REGEX = re.compile(r'^[a-z0-9_\-]+$')  # only lowercase, digits, underscore, hyphen

# Pattern base name rule (no extension): PSW_F_Px_yyyy_zzzz_<anything>
# - x: 1 digit; yyyy: alphanumeric; zzzz: 4 digits; <anything>: at least one char
PATTERN_BASENAME_REGEX = re.compile(r'^PSW_F_P\d+_[^_]+_\d{4}(?:_[A-Za-z0-9]+)+$')


def validate_folder_name(name: str) -> Tuple[bool, str]:
    """Validate feature folder name.

    Rules:
    - Not empty
    - Only lowercase letters, digits, underscore, hyphen
    - Must be all lowercase

    Returns:
        (is_valid, error_message)
    """
    if not name:
        return False, "Folder name cannot be empty."
    if not FOLDER_NAME_REGEX.match(name):
        return False, "Folder name must be lowercase and only contain a-z, 0-9, _, -."
    if not name.islower():
        return False, "Folder name must be all lowercase."
    return True, ""


def normalize_pattern_input(name: str) -> str:
    """Normalize a user-entered pattern name to a base name WITHOUT extension.

    - Trim whitespace
    - If the user includes a trailing '.py' (any case), strip it

    Returns:
        The normalized base name without extension.
    """
    base: str = name.strip()
    if base.lower().endswith(".py"):
        base = base[: -3]  # strip the last 3 chars ('.py')
    return base


def ensure_py_extension(base_name: str) -> str:
    """Return a filename that guarantees a '.py' extension."""
    return f"{base_name}.py"


def validate_pattern_basename(base_name: str) -> Tuple[bool, str]:
    """Validate the pattern base name (without extension).

    Must match: PSW_F_Px_yyyy_zzzz_<anything>

    Returns:
        (is_valid, error_message)
    """
    if not base_name:
        return False, "Filename cannot be empty."
    if not PATTERN_BASENAME_REGEX.match(base_name):
        return False, ("Invalid pattern. Expected base name: PSW_F_Px_yyyy_zzzz_<anything>\n"
                       "Example: PSW_F_P3_ABC_0123_my_case")
    return True, ""


# -----------------------------------------------------------------------------
# GUI application
# -----------------------------------------------------------------------------

class App(tk.Tk):
    """Tkinter main application window."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Feature/Pattern Tool")
        self.geometry("860x660")
        self.minsize(860, 660)

        # State vars
        self.var_status: tk.StringVar = tk.StringVar(value="Ready")
        self.var_folder_name: tk.StringVar = tk.StringVar()
        self.var_dest: tk.StringVar = tk.StringVar(value="")
        self.var_overwrite: tk.BooleanVar = tk.BooleanVar(value=False)

        # Build UI
        self._build_header_paths()
        self._build_tabs()
        self._build_status_bar()

        # Prepare required locations (directories only)
        ensure_dir(FEATURES_ROOT_PATH)
        ensure_parent_dir(PATTERN_TEMPLATE_PATH)       # ensure parent folder exists (not the file)
        ensure_parent_dir(MUTUAL_FUN_TEMPLATE_PATH)    # ensure parent folder exists (not the file)
        # The template files may or may not exist at startup; we check on usage.

    # ------------------- header -------------------
    def _build_header_paths(self) -> None:
        """Builds header showing hard-coded paths and quick-open buttons."""
        frm: ttk.LabelFrame = ttk.LabelFrame(self, text="Paths (Hard-coded, relative to this file)")
        frm.pack(fill="x", padx=12, pady=(12, 8))

        def add_readonly_row(parent: ttk.Misc, label: str, value: Path) -> None: # type: ignore
            row: ttk.Frame = ttk.Frame(parent)
            row.pack(fill="x", padx=8, pady=4)
            ttk.Label(row, text=label).pack(side="left")
            ent: ttk.Entry = ttk.Entry(row)
            ent.insert(0, str(value))
            ent.configure(state="readonly")
            ent.pack(side="left", fill="x", expand=True, padx=6)
            ttk.Button(row, text="Open", command=lambda p=value: self._open_folder(p)).pack(side="left") # type: ignore

        add_readonly_row(frm, "FEATURES_ROOT_PATH:", FEATURES_ROOT_PATH)
        add_readonly_row(frm, "PATTERN_TEMPLATE_PATH (file):", PATTERN_TEMPLATE_PATH)
        add_readonly_row(frm, "MUTUAL_FUN_TEMPLATE_PATH (file):", MUTUAL_FUN_TEMPLATE_PATH)

    def _open_folder(self, path: Path) -> None:
        """Open a folder (or the parent folder if a file path is given) in the OS file browser."""
        try:
            target: Path = path
            if path.is_file():
                target = path.parent
            if sys.platform.startswith("win"):
                os.startfile(target)
            elif sys.platform == "darwin":
                os.system(f'open "{target}"')
            else:
                os.system(f'xdg-open "{target}"')
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder:\n{e}")

    # ------------------- tabs -------------------
    def _build_tabs(self) -> None:
        """Create the tabbed layout."""
        self.tabs: ttk.Notebook = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0, 8))

        # Tab: feature
        tab_feature: ttk.Frame = ttk.Frame(self.tabs)
        self.tabs.add(tab_feature, text="Create Feature Folder")
        self._build_feature_tab(tab_feature)

        # Tab: pattern
        tab_pattern: ttk.Frame = ttk.Frame(self.tabs)
        self.tabs.add(tab_pattern, text="Create Pattern Files")
        self._build_pattern_tab(tab_pattern)

    # ------------------- feature tab -------------------
    def _build_feature_tab(self, parent: tk.Misc) -> None:
        """Build UI for creating feature folders under FEATURES_ROOT_PATH."""
        frm: ttk.Frame = ttk.Frame(parent)
        frm.pack(fill="both", expand=True, padx=16, pady=16)

        ttk.Label(frm, text="Folder name (lowercase; allowed: a-z / 0-9 / _ / -):").pack(anchor="w")
        ttk.Entry(frm, textvariable=self.var_folder_name).pack(fill="x", pady=6)

        btn_row: ttk.Frame = ttk.Frame(frm)
        btn_row.pack(fill="x", pady=6)
        ttk.Button(btn_row, text="Create Folder", command=self.on_create_feature_dir).pack(side="left")
        ttk.Button(btn_row, text="Clear", command=lambda: self.var_folder_name.set("")).pack(side="left", padx=6)

        desc: str = (
            "Creates a folder under FEATURES_ROOT_PATH and adds:\n"
            "  - an empty __init__.py\n"
            "  - a copy of MUTUAL_FUN_TEMPLATE_PATH renamed to mutual_fun.py\n"
            "If the folder already exists, the operation will be aborted."
        )
        ttk.Label(frm, text=desc, foreground="#555").pack(anchor="w", pady=(6, 0))

    def on_create_feature_dir(self) -> None:
        """Create a feature folder under FEATURES_ROOT_PATH and add starter files."""
        name: str = self.var_folder_name.get().strip()

        ok, err = validate_folder_name(name)
        if not ok:
            messagebox.showwarning("Validation Failed", err)
            return

        target: Path = FEATURES_ROOT_PATH / name
        if target.exists():
            messagebox.showerror("Already Exists", f"Folder already exists:\n{target}")
            return

        try:
            # Create target directory structure
            target.mkdir(parents=True, exist_ok=False)

            # 1) Create __init__.py
            init_file: Path = target / "__init__.py"
            init_file.write_text("", encoding="utf-8")

            # 2) Copy mutual_fun_template.py as mutual_fun.py
            try:
                assert_file_exists(MUTUAL_FUN_TEMPLATE_PATH, "mutual_fun template file")
                mutual_fun_target: Path = target / "mutual_fun.py"
                shutil.copy2(MUTUAL_FUN_TEMPLATE_PATH, mutual_fun_target)
            except Exception as e_copy:
                # If mutual fun copy fails, keep the folder created but report the error clearly.
                messagebox.showerror(
                    "Partial Success with Error",
                    f"Folder created and __init__.py added, but failed to copy mutual_fun template:\n{e_copy}"
                )
                self.set_status(f"Created (partial): {target}")
                return

            self.set_status(f"Created: {target}")
            messagebox.showinfo("Success", f"Folder created with __init__.py and mutual_fun.py:\n{target}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create folder:\n{e}")

    # ------------------- pattern tab -------------------
    def _build_pattern_tab(self, parent: tk.Misc) -> None:
        """Build UI for creating pattern files from PATTERN_TEMPLATE_PATH."""
        frm: ttk.Frame = ttk.Frame(parent)
        frm.pack(fill="both", expand=True, padx=16, pady=16)

        # Pattern names input
        name_box: ttk.LabelFrame = ttk.LabelFrame(frm, text="Pattern names (one per line)")
        name_box.pack(fill="both", expand=True)
        ttk.Label(
            name_box,
            text="Rule (no need to type .py): PSW_F_Px_yyyy_zzzz_<anything>"
        ).pack(anchor="w", padx=8, pady=(8, 0))
        self.txt_names: tk.Text = tk.Text(name_box, height=10, wrap="none")
        self.txt_names.pack(fill="both", expand=True, padx=8, pady=8)

        # Destination & options
        dest_box: ttk.LabelFrame = ttk.LabelFrame(frm, text="Destination and Run")
        dest_box.pack(fill="x", pady=(10, 0))

        row2: ttk.Frame = ttk.Frame(dest_box)
        row2.pack(fill="x", padx=8, pady=8)
        ttk.Label(row2, text="Destination folder:").pack(side="left")
        ttk.Entry(row2, textvariable=self.var_dest).pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row2, text="Browse…", command=self._browse_dest).pack(side="left")

        row3: ttk.Frame = ttk.Frame(dest_box)
        row3.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Checkbutton(row3, text="Overwrite if exists", variable=self.var_overwrite).pack(side="left")
        ttk.Button(row3, text="Start Copy", command=self.on_copy_patterns).pack(side="right")

        # Info
        desc: str = (
            "It will copy the fixed template file (PATTERN_TEMPLATE_PATH) to your destination folder, "
            "renaming it to each pattern filename you entered (one per line). "
            "The program will automatically append '.py'."
        )
        ttk.Label(frm, text=desc, foreground="#555").pack(anchor="w", pady=(8, 0))

    def _browse_dest(self) -> None:
        """Open a folder chooser to pick the destination directory."""
        p: str = filedialog.askdirectory(title="Choose destination folder")
        if p:
            self.var_dest.set(p)

    def _collect_names(self) -> List[str]:
        """Collect non-empty raw pattern names from the multi-line text box."""
        raw: str = self.txt_names.get("1.0", "end").strip()
        names: List[str] = []
        for line in raw.splitlines():
            name: str = line.strip()
            if name:
                names.append(name)
        return names

    def _normalize_and_validate_names(self, raw_names: List[str]) -> Tuple[List[str], List[Tuple[str, str]]]:
        """Normalize user-entered names and validate base names.

        Steps per name:
        - Strip whitespace
        - Strip trailing '.py' if present
        - Validate base name against the rule
        - Convert to final filename by appending '.py'

        Returns:
            (valid_filenames_with_py, invalid_list[(original_input, error_message)])
        """
        valid: List[str] = []
        invalid: List[Tuple[str, str]] = []
        for original in raw_names:
            base: str = normalize_pattern_input(original)  # remove .py if any
            ok, err = validate_pattern_basename(base)
            if not ok:
                invalid.append((original, err))
                continue
            final_name: str = ensure_py_extension(base)
            valid.append(final_name)
        return valid, invalid

    def on_copy_patterns(self) -> None:
        """Copy PATTERN_TEMPLATE_PATH to destination for each validated pattern filename."""
        dest_str: str = self.var_dest.get().strip()
        raw_names: List[str] = self._collect_names()
        overwrite: bool = self.var_overwrite.get()

        if not raw_names:
            messagebox.showwarning("Missing Names", "Please enter at least one pattern name (one per line).")
            return
        if not dest_str:
            messagebox.showwarning("Missing Destination", "Please choose a destination folder.")
            return

        # Ensure template file exists now (explicit error if missing)
        try:
            assert_file_exists(PATTERN_TEMPLATE_PATH, "pattern template file")
        except FileNotFoundError as e:
            messagebox.showerror("Missing Template", str(e))
            return

        # Normalize and validate names (convert to *.py)
        valid_names: List[str]
        invalid: List[Tuple[str, str]]
        valid_names, invalid = self._normalize_and_validate_names(raw_names)
        if invalid:
            msg: str = "Some names are invalid:\n\n" + "\n".join([f"- {n}: {e}" for n, e in invalid])
            messagebox.showerror("Validation Failed", msg)
            return

        # Ensure destination exists
        p_dest: Path = Path(dest_str)
        try:
            ensure_dir(p_dest)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create destination folder:\n{e}")
            return

        # Copy loop
        success: List[str] = []
        skipped: List[Tuple[str, str]] = []
        failed: List[Tuple[str, str]] = []
        for n in valid_names:
            target: Path = p_dest / n
            if target.exists() and (not overwrite):
                skipped.append((n, "File already exists"))
                continue
            try:
                shutil.copy2(PATTERN_TEMPLATE_PATH, target)
                success.append(n)
            except Exception as e:
                failed.append((n, str(e)))

        # Summary
        summary: List[str] = [
            f"Success: {len(success)}",
            f"Skipped (exists): {len(skipped)}",
            f"Failed: {len(failed)}",
        ]
        self.set_status(" / ".join(summary))

        detail_lines: List[str] = []
        if success:
            detail_lines.append("Success:\n  - " + "\n  - ".join(success))
        if skipped:
            detail_lines.append("Skipped:\n  - " + "\n  - ".join([f"{n} ({e})" for n, e in skipped]))
        if failed:
            detail_lines.append("Failed:\n  - " + "\n  - ".join([f"{n} ({e})" for n, e in failed]))

        messagebox.showinfo("Result", "\n\n".join(detail_lines) if detail_lines else "No files processed.")

    # ------------------- status bar -------------------
    def _build_status_bar(self) -> None:
        """Create a simple status bar at the bottom."""
        frm: ttk.Frame = ttk.Frame(self)
        frm.pack(fill="x", padx=12, pady=(0, 12))
        ttk.Label(frm, textvariable=self.var_status, foreground="#333").pack(side="left")

    def set_status(self, text: str) -> None:
        """Update status text."""
        self.var_status.set(text)


def main() -> None:
    """Program entry point."""
    app: App = App()
    app.mainloop()


if __name__ == "__main__":
    main()