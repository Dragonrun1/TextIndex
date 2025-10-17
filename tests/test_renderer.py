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
from textindex.renderer import HTMLIndexRenderer


def test_html_renderer_basic(mock_textindex, mock_entry):
    renderer = HTMLIndexRenderer(mock_textindex)
    html = renderer.render()
    assert "<dl" in html
    assert "Apple" in html
    assert "<dt>" in html


def test_html_renderer_with_children(
    mock_textindex, mock_entry, mock_child_entry
):
    # Add child entry
    mock_entry.entries = [mock_child_entry]
    renderer = HTMLIndexRenderer(mock_textindex)
    html = renderer.render()
    assert "Banana" in html
    assert "<dd>" in html  # child container exists


def test_html_renderer_references_and_xrefs(mock_textindex, mock_entry):
    mock_entry._sorted_references.return_value = ["r1", "r2"]
    mock_entry._render_xrefs_of_type.side_effect = (
        lambda t: "xref" if t == "see" else ""
    )
    renderer = HTMLIndexRenderer(mock_textindex)
    html = renderer.render()
    assert "loc-r1" in html
    assert "xref" in html


def test_escape_static_method():
    esc = HTMLIndexRenderer._escape('<>&"')
    assert esc == "&lt;&gt;&amp;&quot;"
    assert HTMLIndexRenderer._escape(None) == ""
