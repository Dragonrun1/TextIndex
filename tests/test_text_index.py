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
from textindex.textindex import TextIndex, TextIndexEntry


# -------------------------------
# Basic creation and parsing tests
# -------------------------------
def test_get_or_create_entry_creates_new(textindex_default):
    parent = None
    entry = textindex_default._get_or_create_entry("TestLabel", parent)
    assert isinstance(entry, TextIndexEntry)
    assert entry.label == "TestLabel"
    assert entry in textindex_default.entries


def test_parse_index_entry_creates_hierarchy(textindex_default):
    entry = textindex_default._parse_index_entry("foo!bar!baz")
    assert entry.label == "baz"
    parent = entry.parent
    assert parent.label == "bar"
    assert parent.parent.label == "foo"


# -------------------------------
# Placeholder and inline HTML tests
# -------------------------------
def test_insert_index_placeholder_replaces_or_appends(textindex_default):
    html = "<p>Content</p>{index}"
    replaced = textindex_default._insert_index_placeholder(html, "<ul></ul>")
    assert "<ul></ul>" in replaced

    html_no_placeholder = "<p>Content</p>"
    replaced = textindex_default._insert_index_placeholder(
        html_no_placeholder, "<ul></ul>"
    )
    assert replaced.endswith("<ul></ul>")


# -------------------------------
# Document preparation and sections
# -------------------------------
def test_prepare_document_normalizes_lines(textindex_default):
    text = "Line1\rLine2\r\nLine3\n"
    prepared = textindex_default._prepare_document(text)
    assert "\r" not in prepared
    assert prepared.count("\n") == 2 + 1  # 3 lines


def test_split_into_sections_stub(textindex_default):
    text = "Line1\nLine2"
    result = textindex_default._split_into_sections(text)
    assert result == text


# -------------------------------
# Post-processing and aliases
# -------------------------------
def test_postprocess_merges_stray_entries(textindex_with_alias):
    # Setup canonical entry and stray
    canonical = TextIndexEntry("tap dance")
    stray = TextIndexEntry("dance")
    stray.references.append({"id": 1})
    textindex_with_alias.entries = [canonical, stray]

    textindex_with_alias._postprocess_entries()
    assert stray not in textindex_with_alias.entries
    assert canonical.references  # references from stray moved


# -------------------------------
# Data-model behaviors
# -------------------------------
def test_bool_and_len_and_str(textindex_sample_hierarchy):
    textindex_sample_hierarchy._indexed_document = "<html></html>"
    assert bool(textindex_sample_hierarchy)
    # length: 3 entries created in fixture
    assert len(textindex_sample_hierarchy) == 3
    s = str(textindex_sample_hierarchy)
    assert "Index (3 entries)" == s


# -------------------------------
# Inline mark processing
# -------------------------------
def test_extract_internal_suffix():
    ti = TextIndex("dummy")
    body, suffix = ti._extract_internal_suffix("term[passim]")
    assert body == "term"
    assert suffix == "passim"

    body, suffix = ti._extract_internal_suffix("no-suffix")
    assert body == "no-suffix"
    assert suffix is None


def test_render_visible_text_emphasis():
    ti = TextIndex("dummy")
    html = ti._render_visible_text("_emphasized_")
    assert html == "<em>emphasized</em>"
    assert ti._render_visible_text("plain") == "plain"


def test_plain_text_strip_markers():
    ti = TextIndex("dummy")
    assert ti._plain_text("_italic_") == "italic"
    assert ti._plain_text("`code`") == "code"
    assert ti._plain_text("plain") == "plain"
