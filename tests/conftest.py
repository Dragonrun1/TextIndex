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
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from textindex.textindex import TextIndex

# -----------------------------
# Fixtures for config.py
# -----------------------------


@pytest.fixture
def tmp_project(fs):
    """Create a temporary project directory in memory."""
    project_root = Path("/example_project")
    project_root.mkdir(parents=True, exist_ok=True)
    (project_root / "example").mkdir(exist_ok=True)
    return project_root


@pytest.fixture
def sample_toml():
    """Minimal TOML string for testing."""
    return textwrap.dedent("""
        [rendering]
        wrap_with_span = true
        emphasis_default = true
        id_prefix = "idx"
        id_counter_start = 1

        [[concordance.rules]]
        pattern = "foo"
        replacement = "bar"

        [[concordance.rules]]
        pattern = "baz"
        replacement = "qux"
    """)


@pytest.fixture
def sample_tsv():
    """Minimal TSV content."""
    return textwrap.dedent("""
        # comment
        foo\tbar
        baz\tqux
    """)


# -----------------------------
# Fixtures for renderer.py
# -----------------------------


@pytest.fixture
def mock_entry():
    """Minimal mock TextIndexEntry for renderer testing."""
    entry = MagicMock()
    entry.entry_id = 1
    entry.label = "Apple"
    entry.entries = []
    entry._entry_id_prefix = "idx"
    entry._render_xrefs_of_type.return_value = ""
    entry._sorted_references.return_value = []
    entry._build_locator_html.side_effect = lambda ref: f"loc-{ref}"
    return entry


@pytest.fixture
def mock_child_entry():
    """Mock child entry for nested index testing."""
    child = MagicMock()
    child.entry_id = 2
    child.label = "Banana"
    child.entries = []
    child._entry_id_prefix = "idx"
    child._render_xrefs_of_type.return_value = ""
    child._sorted_references.return_value = []
    child._build_locator_html.side_effect = lambda ref: f"loc-{ref}"
    return child


@pytest.fixture
def mock_textindex(mock_entry):
    """Minimal mock TextIndex containing entries."""
    ti = MagicMock()
    ti.entries = [mock_entry]
    ti.sort_entries.side_effect = lambda entries: entries
    ti.group_heading.side_effect = (
        lambda initial, is_first=False: f"<h>{initial}</h>"
    )
    ti._prefix = "see"
    ti._also = "also"
    return ti


# -----------------------------
# Fixtures for textindex.py
# -----------------------------


@pytest.fixture
def textindex_default():
    """Return a fresh TextIndex instance with default config."""
    sample_text = """
    This is a sample document.

    Here is an index mark: {^foo}.
    Another mark: [Bar]{^bar}.
    """
    return TextIndex(sample_text)


@pytest.fixture
def textindex_with_alias():
    """TextIndex with an alias pre-defined."""
    ti = TextIndex("Some text with alias")
    ti._alias_book = {"td": ["tap dance"]}
    return ti


@pytest.fixture
def textindex_sample_hierarchy():
    """TextIndex instance with hierarchical entries already created."""
    ti = TextIndex("Hierarchical sample")
    e1, _ = ti.entry_at_path("foo", [], True)
    e2, _ = ti.entry_at_path("bar", ["foo"], True)
    e3, _ = ti.entry_at_path("baz", ["foo", "bar"], True)
    return ti
