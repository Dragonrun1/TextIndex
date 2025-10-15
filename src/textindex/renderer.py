#  TextIndex - A simple, lightweight syntax for creating indexes in text documents.
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

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .textindex import TextIndex, TextIndexEntry


class HTMLIndexRenderer:
    """Renders a TextIndex as an HTML unordered list (<ul>/<li>) hierarchy."""

    def __init__(self, textindex: "TextIndex"):
        self.textindex = textindex
        self.config = textindex.config

    # ------------------------------------------------------------------
    # Public rendering entry points
    # ------------------------------------------------------------------
    def render(self) -> str:
        """Render the entire index hierarchy to HTML."""
        html = "<ul class='text-index'>"
        for entry in self.textindex.entries:
            html += self.render_entry(entry)
        html += "</ul>"
        return html

    def render_entry(self, entry: "TextIndexEntry", level: int = 0) -> str:
        """Render a single entry and its subentries recursively."""
        label_html = self._escape(entry.label or "")
        refs_html = entry.render_references() or ""
        cross_html = entry.render_cross_references() or ""
        also_html = entry.render_also_references() or ""

        content = label_html
        if refs_html:
            content += f" {refs_html}"
        if cross_html:
            content += f" — {self.config.see_label} {cross_html}"
        if also_html:
            content += f" — {self.config.see_also_label} {also_html}"

        html = f"<li class='level-{level}'>{content}"

        if entry.entries:
            html += "<ul>"
            for child in entry.entries:
                html += self.render_entry(child, level + 1)
            html += "</ul>"

        html += "</li>"
        return html

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _escape(text: str) -> str:
        """Escape HTML-sensitive characters."""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )
