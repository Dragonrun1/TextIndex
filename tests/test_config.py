# noqa: D100
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
import textwrap
import tomllib
from pathlib import Path

import pytest
from textindex.config import (
    ConcordanceRule,
    IndexConfig,
    ProjectConfig,
    load_project_config,
)


def test_concordance_rule_normalizes_empty_strings():
    rule = ConcordanceRule(pattern="foo", replacement="", comment="")
    assert rule.replacement is None
    assert rule.comment is None


def test_project_config_from_toml(sample_toml):
    data = tomllib.loads(sample_toml)
    cfg = ProjectConfig.from_toml(data)

    assert isinstance(cfg.rendering, IndexConfig)
    assert cfg.rendering.wrap_with_span is True
    assert len(cfg.concordance_rules) == 2
    assert cfg.concordance_rules[0].pattern == "foo"
    assert cfg.concordance_rules[0].replacement == "bar"


def test_project_config_from_tsv(sample_tsv):
    rows = [line.split("\t") for line in sample_tsv.strip().splitlines()]
    cfg = ProjectConfig.from_tsv(rows)

    assert len(cfg.concordance_rules) == 2
    patterns = [r.pattern for r in cfg.concordance_rules]
    assert "foo" in patterns
    assert "baz" in patterns


def test_load_project_config_prefers_toml(fs, sample_toml, sample_tsv):
    """TOML overrides TSV."""
    base = Path("/project")
    example = base / "example"
    example.mkdir(parents=True)

    (example / "textindex-config.toml").write_text(
        sample_toml, encoding="utf-8"
    )
    (example / "example-concordance.tsv").write_text(
        sample_tsv, encoding="utf-8"
    )

    cfg = load_project_config(base)
    assert isinstance(cfg, ProjectConfig)
    assert len(cfg.concordance_rules) == 2
    assert cfg.concordance_rules[0].replacement == "bar"


def test_load_project_config_fallback_to_tsv(fs, sample_tsv):
    """TSV used if TOML missing."""
    base = Path("/project")
    example = base / "example"
    example.mkdir(parents=True)

    (example / "example-concordance.tsv").write_text(
        sample_tsv, encoding="utf-8"
    )

    cfg = load_project_config(base)
    assert len(cfg.concordance_rules) == 2
    assert cfg.concordance_rules[0].pattern == "foo"


def test_load_project_config_defaults_when_missing(fs):
    base = Path("/project")
    (base / "example").mkdir(parents=True)
    cfg = load_project_config(base)
    assert isinstance(cfg, ProjectConfig)
    assert cfg.concordance_rules == []
    assert isinstance(cfg.rendering, IndexConfig)


# -----------------------------
# Edge Case Tests
# -----------------------------


def test_project_config_from_toml_with_missing_fields():
    toml_data = tomllib.loads("""
        [rendering]
        wrap_with_span = true
    """)
    cfg = ProjectConfig.from_toml(toml_data)
    assert cfg.rendering.wrap_with_span is True
    assert cfg.rendering.emphasis_default is True
    assert cfg.concordance_rules == []


def test_project_config_from_tsv_with_blank_and_comment_rows(sample_tsv):
    rows = [
        [],
        ["# just a comment"],
        ["foo", "bar"],
        ["baz", "qux"],
        ["   "],
    ]
    cfg = ProjectConfig.from_tsv(rows)
    assert len(cfg.concordance_rules) == 2
    patterns = [r.pattern for r in cfg.concordance_rules]
    assert "foo" in patterns
    assert "baz" in patterns


def test_load_project_config_with_malformed_toml(fs):
    base = Path("/project")
    example = base / "example"
    example.mkdir(parents=True)
    (example / "textindex-config.toml").write_text(
        "invalid-toml", encoding="utf-8"
    )

    import tomllib

    with pytest.raises(tomllib.TOMLDecodeError):
        load_project_config(base)


def test_load_project_config_with_empty_tsv(fs):
    base = Path("/project")
    example = base / "example"
    example.mkdir(parents=True)
    (example / "example-concordance.tsv").write_text(
        "\n\n  #comment\n", encoding="utf-8"
    )

    cfg = load_project_config(base)
    assert isinstance(cfg, ProjectConfig)
    assert cfg.concordance_rules == []


def test_concordance_rules_with_duplicate_patterns():
    rows = [["foo", "bar"], ["foo", "baz"]]
    cfg = ProjectConfig.from_tsv(rows)
    assert len(cfg.concordance_rules) == 2
    assert cfg.concordance_rules[0].pattern == "foo"
    assert cfg.concordance_rules[0].replacement == "bar"
    assert cfg.concordance_rules[1].pattern == "foo"
    assert cfg.concordance_rules[1].replacement == "baz"


# -----------------------------
# load_project_config Priority & Fallback Tests
# -----------------------------


def test_load_project_config_toml_overrides_empty_tsv(fs, sample_toml):
    base = Path("/project")
    example = base / "example"
    example.mkdir(parents=True)

    (example / "textindex-config.toml").write_text(
        sample_toml, encoding="utf-8"
    )
    (example / "example-concordance.tsv").write_text("\n", encoding="utf-8")

    cfg = load_project_config(base)
    assert len(cfg.concordance_rules) == 2
    assert cfg.concordance_rules[0].pattern == "foo"


def test_load_project_config_only_tsv(fs, sample_tsv):
    base = Path("/project")
    example = base / "example"
    example.mkdir(parents=True)

    (example / "example-concordance.tsv").write_text(
        sample_tsv, encoding="utf-8"
    )

    cfg = load_project_config(base)
    assert len(cfg.concordance_rules) == 2
    assert cfg.concordance_rules[1].pattern == "baz"


def test_load_project_config_toml_with_partial_concordance(fs):
    base = Path("/project")
    example = base / "example"
    example.mkdir(parents=True)

    toml_content = textwrap.dedent("""
        [rendering]
        wrap_with_span = true
        emphasis_default = false
    """)
    (example / "textindex-config.toml").write_text(
        toml_content, encoding="utf-8"
    )

    cfg = load_project_config(base)
    assert isinstance(cfg, ProjectConfig)
    assert cfg.concordance_rules == []
    assert cfg.rendering.wrap_with_span is True
    assert cfg.rendering.emphasis_default is False


def test_load_project_config_neither_file_exists(fs):
    base = Path("/project")
    example = base / "example"
    example.mkdir(parents=True)

    cfg = load_project_config(base)
    assert isinstance(cfg, ProjectConfig)
    assert cfg.concordance_rules == []
    assert cfg.rendering.wrap_with_span is True


# -----------------------------
# Coverage-gap Tests
# -----------------------------


def test_load_project_config_toml_no_tsv(fs, sample_toml):
    """TOML exists, TSV missing → print branch executed."""
    base = Path("/project")
    example = base / "example"
    example.mkdir(parents=True)

    (example / "textindex-config.toml").write_text(
        sample_toml, encoding="utf-8"
    )
    # TSV not created

    cfg = load_project_config(base)
    assert len(cfg.concordance_rules) == 2


def test_parse_concordance_from_tsv_rows_with_empty_columns():
    """TSV row with only blank columns is skipped."""
    from textindex.config import _parse_concordance_from_tsv_rows

    rows = [["", "", ""]]
    rules = _parse_concordance_from_tsv_rows(rows)
    assert rules == []
