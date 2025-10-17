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


def test_process_inline_marks_with_alias(textindex_default):
    # Invisible mark that defines alias
    doc = "This is a test {^##myalias}."
    out = textindex_default._process_inline_marks(doc)
    assert "span" in out or out  # At least some output generated
    assert "myalias" in textindex_default._alias_book


def test_process_inline_marks_xref_only(textindex_default):
    doc = "Xref only {^|other entry}."
    out = textindex_default._process_inline_marks(doc)
    assert "span" in out
    # Entry should have cross_reference
    entry = textindex_default.entries[0]
    assert entry.cross_references


def test_parse_mark_body_flags_and_aliases(textindex_default):
    body = 'Path > Segment! / ##def #ref | ref1; + ref2 ~"sortkey"'
    result = textindex_default._parse_mark_body(body)
    assert result["emphasis"]
    assert result["continuing"]
    assert result["alias_def"] == "def"
    assert result["alias_ref"] == "ref"
    assert result["see"]
    assert result["see_also"]
    assert result["sort_key"] == "sortkey"


def test_postprocess_merges_stray(textindex_with_alias):
    # Create stray entry "dance" manually
    ti = textindex_with_alias
    stray = ti._get_or_create_entry("dance", None)
    stray.references.append({"id": 999})
    ti._postprocess_entries()
    td_path = ti._alias_book["td"]
    td_entry = ti.existing_entry_at_path(td_path)
    assert any(ref["id"] == 999 for ref in td_entry.references)
    # Ensure stray removed from top-level
    top_labels = [e.label for e in ti.entries]
    assert "dance" not in top_labels


def test_process_wildcards_label_only(textindex_default):
    # Add entry to allow prefix search
    ti = textindex_default
    ti._get_or_create_entry("foobar", None)
    out = ti.process_wildcards("foobar", "See *^")
    assert "foobar" in out


def test_render_markdown_heading_with_attrs(textindex_default):
    heading = "# Title .class1 #myid key=value"
    html = textindex_default.render_markdown_heading(heading)
    assert 'id="myid"' in html
    assert 'class="class1"' in html
    assert 'key="value"' in html


def test_insert_index_placeholder_append(textindex_default):
    ti = textindex_default
    doc = "No placeholder here."
    out = ti._insert_index_placeholder(doc, "<index>HTML</index>")
    assert out.endswith("<index>HTML</index>")


def test_insert_index_placeholder_replace(textindex_default):
    ti = textindex_default
    doc = "Here is {index} marker."
    out = ti._insert_index_placeholder(doc, "<index>HTML</index>")
    assert "<index>HTML</index>" in out
