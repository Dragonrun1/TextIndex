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
from types import SimpleNamespace

import pytest
from textindex.textindex import TextIndexEntry


# -----------------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------------
@pytest.fixture
def mock_textindex():
    """Lightweight mock of the TextIndex class used by TextIndexEntry."""
    return SimpleNamespace(
        _ref_type="ref-type",
        _path="path",
        _reference="reference",
        _also="also",
        _path_delimiter=">",
        index_id_prefix="idx",
        config=SimpleNamespace(
            field_separator=", ",
            list_separator="; ",
            path_separator=": ",
            range_separator="–",
            see_label="see",
            see_also_label="see also",
        ),
        section_mode=False,
        sort_emphasis_first=False,
        inform=lambda *args, **kwargs: None,
        existing_entry_at_path=lambda path: None,
    )


@pytest.fixture
def entry(mock_textindex):
    """Create a basic TextIndexEntry."""
    return TextIndexEntry(label="Alpha", textindex=mock_textindex)


# -----------------------------------------------------------------------------
# Core functionality
# -----------------------------------------------------------------------------
def test_entry_id_increments(entry):
    e1 = TextIndexEntry(label="A")
    e2 = TextIndexEntry(label="B")
    assert e2.entry_id == e1.entry_id + 1


def test_add_reference(entry):
    entry.add_reference(start_id="p1")
    assert len(entry.references) == 1
    ref = entry.references[0]
    assert ref["start-id"] == "p1"
    assert ref["ref-type"] == entry.textindex._reference


def test_add_cross_reference(entry):
    entry.add_cross_reference("see", ["Topic", "Subtopic"])
    assert len(entry.cross_references) == 1
    ref = entry.cross_references[0]
    assert ref["ref-type"] == "see"
    assert ref["path"] == ["Topic", "Subtopic"]


def test_depth_and_path(entry):
    parent = TextIndexEntry(label="Root", textindex=entry.textindex)
    child = TextIndexEntry(
        label="Child", parent=parent, textindex=entry.textindex
    )
    assert child.depth() == 1
    assert child.path_list() == ["Root", "Child"]


# -----------------------------------------------------------------------------
# Rendering
# -----------------------------------------------------------------------------
def test_render_references_basic(entry):
    """Should render a simple <a> tag for each reference."""
    entry.add_reference("1")
    html = entry.render_references()
    assert '<a class="locator"' in html
    assert 'href="#idx1"' in html


def test_render_references_with_emphasis(entry):
    """Should wrap in <em> when locator_emphasis=True."""
    entry.add_reference("1", locator_emphasis=True)
    html = entry.render_references()
    assert "<em>" in html
    assert "</em>" in html


def test_render_references_with_range(entry):
    """Should add range separator when both start and end IDs exist."""
    entry.add_reference("1")
    entry.references[0]["end-id"] = "3"
    html = entry.render_references()
    assert "–" in html  # range separator


def test_render_cross_references(entry):
    """Should render linked HTML for 'see' references."""
    entry.cross_references.append(
        {
            "ref-type": "see",
            "path": ["Foo", "Bar"],
        }
    )
    # Mock existing_entry_at_path to simulate found reference
    entry.textindex.existing_entry_at_path = lambda path: TextIndexEntry(
        "Ref", entry.textindex
    )
    html = entry.render_cross_references()
    assert '<a class="entry-link"' in html
    assert "Foo: Bar" in html


def test_render_also_references(entry):
    """Should render 'see also' type references."""
    entry.cross_references.append(
        {
            "ref-type": "also",
            "path": ["Another", "Thing"],
        }
    )
    entry.textindex._also = "also"
    html = entry.render_also_references()
    assert "Another: Thing" in html


def test_deduplication_section_mode(entry):
    """Section-mode refs with same start/end should be deduped."""
    entry.textindex.section_mode = True
    entry.add_reference("1")
    entry.add_reference("2")
    # force duplicate pair
    for ref in entry.references:
        ref["start-section"] = "A"
        ref["start-end"] = "B"
    deduped = entry._dedupe_section_refs(entry.references)
    assert len(deduped) == 1


def test_sorting_of_cross_refs(entry):
    """Cross-references should sort alphabetically by path then type."""
    entry.cross_references.extend(
        [
            {"ref-type": "also", "path": ["B"]},
            {"ref-type": "see", "path": ["A"]},
        ]
    )
    entry._sort_cross_refs()
    # After sorting: by path (A before B), then see before also
    assert entry.cross_references[0]["path"] == ["A"]
