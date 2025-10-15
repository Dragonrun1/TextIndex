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
    """Render TextIndex entries into an HTML <dl> list hierarchy."""

    def __init__(self, textindex: "TextIndex"):
        self.textindex = textindex
        self.config = textindex.config

    def render(self) -> str:
        """Render full index as <dl>…</dl> HTML."""
        html = "<dl class='textindex'>\n"
        for entry in getattr(self.textindex, "entries", []):
            html += self.render_entry(entry)
        html += "</dl>\n"
        return html

    def render_entry(self, entry: "TextIndexEntry", level: int = 0) -> str:
        """Render a single index entry line."""
        # Handle missing label gracefully
        label = getattr(entry, "label", "?")
        parsed = self._parse_index_entry_text(label)

        html = "<dt>"
        html += self._escape(parsed["main"])

        # Subentries
        for sub in parsed["subs"]:
            html += f" &gt; {self._escape(sub)}"

        # See / See also
        see_bits = []
        if parsed["seealso"]:
            see_bits.append(
                "<i>see</i> " + self._escape("; ".join(parsed["seealso"]))
            )
        if parsed["seealso_also"]:
            see_bits.append(
                "<i>see also</i> "
                + self._escape("; ".join(parsed["seealso_also"]))
            )
        if see_bits:
            html += " — " + "; ".join(see_bits)

        html += "</dt>\n"
        return html

    @staticmethod
    def _escape(text: str) -> str:
        """Escape HTML special characters."""
        if text is None:
            return ""
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    @staticmethod
    def _parse_index_entry_text(text: str) -> dict[str, list[str] | str]:
        """Parse a raw index directive body into components.

        Handles hierarchy (>), cross-references (|), and list separators (;).
        Example: 'layers>"Shift, concept of"##shiftlayer|+safety'
        """
        entry = {"main": "", "subs": [], "seealso": [], "seealso_also": []}

        # Separate 'see' and 'see also' portions
        see_split = text.split("|")
        main = see_split[0].strip()
        if len(see_split) > 1:
            for seg in see_split[1:]:
                seg = seg.strip()
                if not seg:
                    continue
                # '+…' means "see also"
                if seg.startswith("+"):
                    entry["seealso_also"].extend(
                        [s.strip() for s in seg[1:].split(";") if s.strip()]
                    )
                else:
                    entry["seealso"].extend(
                        [s.strip() for s in seg.split(";") if s.strip()]
                    )

        # Split hierarchical terms
        parts = [p.strip() for p in main.split(">") if p.strip()]
        entry["main"] = parts[0] if parts else ""
        if len(parts) > 1:
            entry["subs"] = parts[1:]

        return entry
