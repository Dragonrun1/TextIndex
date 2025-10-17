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
from typing import Iterable, Literal, Optional, Type


@dataclass(slots=True)
class ConcordanceRule:
    """Represents a single pattern→replacement rule in a concordance.

    Attributes:
        pattern : str
            Regex or literal match pattern (case sensitivity inferred or
            enforced by `=` prefix).
        replacement : Optional[str]
            Text or markup to insert for matches. May include index mark syntax.
        comment : Optional[str]
            Optional explanation or inline documentation.
    """

    pattern: str
    replacement: Optional[str] = None
    comment: Optional[str] = None

    def __post_init__(self):
        # Normalize empty strings to None for consistency.
        if self.replacement == "":
            self.replacement = None
        if self.comment == "":
            self.comment = None


@dataclass(slots=True)
class IndexConfig:
    """Configuration options for text index generation and rendering."""

    case_sensitive_sort: bool = False
    category_separator: str = ". "
    emphasis_default: bool = True
    field_separator: str = ", "
    footer_text: str = ""
    group_headings: bool = False
    header_text: str = "<h2>Index</h2>"
    id_counter_start: int = 1
    id_prefix: str = "idx"
    include_footer: bool = False
    include_header: bool = False
    list_separator: str = "; "
    output_format: Literal["html", "markdown", "text"] = "html"
    path_separator: str = ": "
    range_separator = "–"
    run_in_children: bool = True
    section_mode: bool = False
    see_also_label: str = "see also"
    see_label: str = "see"
    show_warnings: bool = True
    sort_emphasis_first: bool = False
    verbose: bool = False
    wrap_with_span: bool = True


@dataclass(slots=True)
class ProjectConfig:
    """Unified configuration combining rendering and concordance rules."""

    rendering: IndexConfig = field(default_factory=IndexConfig)
    concordance_rules: list[ConcordanceRule] = field(default_factory=list)

    @classmethod
    def from_toml(cls: Type["ProjectConfig"], data: dict) -> "ProjectConfig":
        """Construct a ProjectConfig from a parsed TOML dictionary.

        Expects TOML schema:
            [rendering]
            [[concordance.rules]]
        """
        rendering = IndexConfig(**data.get("rendering", {}))
        concordance_rules = _parse_concordance_from_toml(data)
        return cls(rendering, concordance_rules)

    @classmethod
    def from_tsv(cls, rows: Iterable[list[str]]) -> "ProjectConfig":
        """Create configuration from TSV rows."""
        # Use defaults; TSV doesn’t include rendering options
        rendering = IndexConfig()
        concordance_rules = _parse_concordance_from_tsv_rows(rows)
        return cls(rendering, concordance_rules)


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
    if isinstance(base_path, str):
        base_path = Path(base_path.strip())
    toml_path = base_path / "example" / "textindex-config.toml"
    tsv_path = base_path / "example" / "example-concordance.tsv"

    # --- Prefer TOML ---
    if toml_path.is_file():
        print(f"[TextIndex] Using configuration from '{toml_path.name}'.")
        if tsv_path.is_file():
            mess = (
                "[TextIndex] Ignoring legacy concordance at"
                f" {tsv_path.name} (TOML override found)."
            )
            print(mess)

        with toml_path.open("rb") as f:
            data = tomllib.load(f)

        return ProjectConfig.from_toml(data)

    # --- Fallback to legacy TSV ---
    if tsv_path.is_file():
        mess = (
            "[TextIndex] No TOML config found."
            f" Loading legacy concordance from {tsv_path.name}."
        )
        print(mess)

        with tsv_path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            rows = list(reader)

        return ProjectConfig.from_tsv(rows)

    # --- Nothing found ---
    mess = (
        "[TextIndex] Info: No configuration file found in "
        f"'{base_path.resolve()}'. Using defaults."
    )
    print(mess)
    return ProjectConfig()


def _parse_concordance_from_toml(data: dict) -> list[ConcordanceRule]:
    """Parse concordance rules from a TOML dict."""
    rules_data = data.get("concordance", {}).get("rules", [])
    rules: list[ConcordanceRule] = []

    for entry in rules_data:
        rules.append(
            ConcordanceRule(
                pattern=entry.get("pattern", ""),
                replacement=entry.get("replacement"),
                comment=entry.get("comment"),
            )
        )
    return rules


def _parse_concordance_from_tsv_rows(
    rows: Iterable[list[str]],
) -> list[ConcordanceRule]:
    """Parse concordance rules from TSV lines, ignoring comments and blanks."""
    rules: list[ConcordanceRule] = []
    for row in rows:
        if not row or not row[0].strip() or row[0].strip().startswith("#"):
            continue  # Skip comments or blank lines

        parts = [col.strip() for col in row if col.strip()]
        if not parts:
            continue

        pattern = parts[0]
        replacement = parts[1] if len(parts) > 1 else None
        rules.append(ConcordanceRule(pattern=pattern, replacement=replacement))

    return rules
