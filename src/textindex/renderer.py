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
"""xxx."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .textindex import TextIndex, TextIndexEntry


class HTMLIndexRenderer:
    """Render TextIndex entries into an HTML <dl> hierarchy."""

    def __init__(self, textindex: "TextIndex"):
        self.textindex = textindex
        self.config = textindex.config

    def render(self) -> str:
        """Render the full index as <dl class="textindex index">…</dl>."""
        entries = self.textindex.sort_entries(self.textindex.entries)
        html = '<dl class="textindex index">\n'
        prev_initial = None
        is_first = True
        for ent in entries:
            initial = (ent.sort_on()[:1] or "").upper()
            # Group separators (blank line entries) between groups
            if prev_initial is not None and initial != prev_initial:
                html += self.textindex.group_heading(initial)
            elif is_first:
                html += self.textindex.group_heading(initial, is_first=True)
            is_first = False
            prev_initial = initial

            html += self._render_entry(ent)
        html += "</dl>\n"
        return html

    def _render_entry(self, entry: "TextIndexEntry") -> str:
        html = "\t<dt>"
        html += f'<span id="{entry._entry_id_prefix}{entry.entry_id}" class="entry-heading">{self._escape(entry.label)}</span>'
        # References (locators)
        refs_html = self._render_references(entry)
        xref_see = entry._render_xrefs_of_type(self.textindex._prefix)
        xref_also = entry._render_xrefs_of_type(self.textindex._also)
        xref_bits = []
        if xref_see:
            xref_bits.append(
                f"<em>{self.config.see_label.capitalize()}</em> {xref_see}"
            )
        if xref_also:
            xref_bits.append(
                f"<em>{self.config.see_also_label.capitalize()}</em> {xref_also}"
            )
        # Render refs/xrefs: if entry has children, put xrefs as separate child DT
        if refs_html:
            html += f'<span class="entry-references">, {refs_html}'
            # If we add xrefs here (no children), punctuation handled below
            if not entry.entries and xref_bits:
                html += f". {'. '.join(xref_bits)}"
            html += "</span>"
        else:
            if not entry.entries and xref_bits:
                html += f'<span class="entry-references">. {". ".join(xref_bits)}</span>'
        html += "</dt>\n"

        # Children
        if entry.entries:
            html += "\t<dd>\n\t\t<dl>\n"
            # If there are xrefs, render them as a separate child row first
            if xref_bits:
                html += (
                    '\t\t\t<dt><span class="entry-references">'
                    + " . ".join(xref_bits)
                    + "</span></dt>\n"
                )
            for child in self.textindex.sort_entries(entry.entries):
                html += "\t\t\t" + self._render_entry(child)
            html += "\t\t</dl>\n\t</dd>\n"

        return html

    def _render_references(self, entry: "TextIndexEntry") -> str | None:
        refs = entry._sorted_references()
        if not refs:
            return None
        parts = [entry._build_locator_html(ref) for ref in refs]
        return ", ".join(parts)

    @staticmethod
    def _escape(text: str) -> str:
        if text is None:
            return ""
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
