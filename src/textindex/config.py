#  TextIndex - A simple, lightweight syntax for creating indexes in text
#  documents.
#  Copyright © 2025 Michael Cummings <mgcummings@yahoo.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
#  SPDX-License-Identifier: GPL-3.0-or-later
# ##############################################################################
"""Configuration related code."""

from __future__ import annotations

import csv
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Literal


@dataclass
class IndexConfig:
    """Configuration options for text index generation and rendering."""

    # --- Labels ---
    see_label: str = "see"
    see_also_label: str = "see also"

    # --- Rendering behavior ---
    category_separator: str = ". "
    field_separator: str = ", "
    list_separator: str = "; "
    path_separator: str = ": "
    range_separator = "–"
    wrap_with_span: bool = True
    emphasis_default: bool = True
    id_prefix: str = "idx"
    id_counter_start: int = 1

    # --- Structural behavior ---
    run_in_children: bool = True
    # Legacy example output does not show visible A/Z headings;
    # keep only NBSP separators by default.
    group_headings: bool = False
    sort_emphasis_first: bool = False

    # --- Output format ---
    # Literal["html", "markdown", "text"]
    output_format: Literal["html", "markdown", "text"] = "html"

    # --- Logging and diagnostics ---
    verbose: bool = False
    show_warnings: bool = True

    # --- Advanced options ---
    section_mode: bool = False
    case_sensitive_sort: bool = False

    # --- Optional header/footer support ---
    include_header: bool = False
    include_footer: bool = False
    header_text: str = "<h2>Index</h2>"
    footer_text: str = ""


@dataclass
class ProjectConfig:
    rendering: IndexConfig = field(default_factory=IndexConfig)
    concordance_rules: List[Dict[str, Any]] = field(default_factory=list)


def load_project_config(base_path: str | Path) -> ProjectConfig:
    """Load TextIndex configuration.

    Priority:
      1. textindex-config.toml (preferred modern format)
      2. example-concordance.tsv (legacy fallback)

    Args:
        base_path(str | Path): Directory containing configuration files.

    Returns:
        ProjectConfig instance with rendering and concordance rules populated.
    """
    base = Path(base_path)
    toml_path = base / "textindex-config.toml"
    tsv_path = base / "example-concordance.tsv"

    # --- Prefer TOML ---
    if toml_path.is_file():
        print(f"[TextIndex] Using configuration from '{toml_path}'.")

        with toml_path.open("rb", encoding="utf-8") as f:
            data = tomllib.load(f)

        rendering = IndexConfig(**data.get("rendering", {}))
        rules = data.get("concordance", {}).get("rules", [])
        return ProjectConfig(rendering=rendering, concordance_rules=rules)

    # --- Fallback to legacy TSV ---
    if tsv_path.is_file():
        print(f"[TextIndex] Using legacy configuration from '{tsv_path}'.")

        rules: list[dict[str, str]] = []
        with tsv_path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            for line in reader:
                # Skip blanks and comments
                if not line or line[0].strip().startswith("#"):
                    continue

                pattern = line[0].strip()
                replacement = line[1].strip() if len(line) > 1 else ""
                rules.append({"pattern": pattern, "replacement": replacement})

        return ProjectConfig(concordance_rules=rules)

    # --- Nothing found ---
    mess = (
        "[TextIndex] Info: No configuration file found in "
        f"'{base.resolve()}'. Using defaults."
    )
    print(mess)
    return ProjectConfig()
