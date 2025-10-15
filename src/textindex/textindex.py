#  TextIndex - A simple, lightweight syntax for creating indexes in text documents.
#  Copyright © 2025 Matt Gemmell
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
"""Inserts an index into an appropriately-formatted text document.

Examples:
    >>> from textindex import textindex
    >>> index = textindex.TextIndex("Hello World")
    >>> index.verbose = True
    >>> book_contents_string = index.indexed_document()
    TextIndex: 0 entries created.

Usage:
 from textindex import textindex
 index = textindex.TextIndex(book_contents_string)
 index.verbose = True # To see a LOT of output!
 book_contents_string = index.indexed_document()

 Or if you just want the (HTML formatted) index itself:
 from textindex import textindex
 index = textindex.TextIndex(book_contents_string)
 index_html = index.index_html()
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, fields
from typing import (
    Any,
    Dict,
    List,
    Literal,
    Optional,
    Self,
    Tuple,
)

from textindex.renderer import HTMLIndexRenderer


def emphasis(text: str, remove: bool = False) -> str:
    """Change emphasis on text.

    Args:
        text (str): text to modify.
        remove (bool): remove the emphasis.

    Returns:
        str: modified text.
    """
    # Process Markdown _emphasis_
    replace_val = r"<em>\1</em>" if not remove else r"\1"
    return re.sub(r"_([^_]+?)_", replace_val, text)


def elide_end(start: int, end: int) -> int:
    """Elide the end of a range as much as possible.

    An Exception is made for teens.
    This is a pragmatic approximation of the Chicago Manual of Style convention.

    Args:
        start (int): start index.
        end (int): end index.

    Returns:
        int: end index.
    """
    start_str = str(start)
    end_str = str(end)
    result = end_str
    start_len = len(start_str)
    end_len = len(end_str)
    if start_len == end_len and start_len > 1 and start != end:
        # Trim leftmost matching digits of start/end.
        cut = 0
        while start_str[cut] == end_str[cut]:
            cut += 1
        # Special case: if the numbers are teens (i.e. second-last digit is 1),
        # retain the 1.
        if end_len > 1 and cut == end_len - 1 and end_str[-2] == "1":
            cut -= 1
        result = end_str[cut:]

    return int(result)


@dataclass
class IndexConfig:
    """Configuration options for text index generation and rendering."""

    # --- Labels ---
    see_label: str = "see"
    see_also_label: str = "see also"

    # --- Rendering behavior ---
    category_separator: str = ". "
    field_separator: str = ", "
    list_separator: str = "; "
    path_separator: str = ": "
    range_separator = "–"

    # --- Structural behavior ---
    run_in_children: bool = True
    group_headings: bool = True
    sort_emphasis_first: bool = False

    # --- Output format ---
    output_format: str = Literal["html", "markdown", "text"]

    # --- Logging and diagnostics ---
    verbose: bool = False
    show_warnings: bool = True

    # --- Advanced options ---
    section_mode: bool = False
    case_sensitive_sort: bool = False


@dataclass
class TextIndexEntry:
    """Represents a single entry in a text index hierarchy."""

    label: Optional[str] = None
    parent: Optional[Self] = None
    textindex: Optional[Any] = None
    sort_key: Optional[str] = None

    entries: List[Self] = field(default_factory=list)
    references: List[Dict[str, Any]] = field(default_factory=list)
    cross_references: List[Dict[str, Any]] = field(default_factory=list)

    # class-level constants
    _entry_id_prefix: str = field(default="entry", init=False, repr=False)
    _entry_link_class: str = field(default="entry-link", init=False, repr=False)
    _next_id: int = 0

    end_id: str = field(default="end-id", init=False, repr=False)
    end_suffix: str = field(default="end-suffix", init=False, repr=False)
    locator_emphasis: str = field(
        default="locator-emphasis", init=False, repr=False
    )
    section_end: str = field(default="start-end", init=False, repr=False)
    section_start: str = field(default="start-section", init=False, repr=False)
    start_id: str = field(default="start-id", init=False, repr=False)
    suffix: str = field(default="suffix", init=False, repr=False)

    entry_id: int = field(init=False)

    # ---------------------------------------------------------------------
    # Initialization
    # ---------------------------------------------------------------------
    def __post_init__(self) -> None:
        """Assign a unique ID to each entry instance."""
        self.entry_id = TextIndexEntry._next_id
        TextIndexEntry._next_id += 1

    # ---------------------------------------------------------------------
    # Core behavior
    # ---------------------------------------------------------------------
    def add_cross_reference(self, ref_type: str, path: str) -> None:
        """Add a cross-reference if not already present."""
        for ref in self.cross_references:
            if (
                ref[self.textindex._ref_type] == ref_type
                and ref[self.textindex._path] == path
            ):
                return
        self.cross_references.append(
            {self.textindex._ref_type: ref_type, self.textindex._path: path}
        )

    def add_reference(
        self,
        start_id: str,
        suffix: Optional[str] = None,
        locator_emphasis: bool = False,
        section: Optional[str] = None,
    ) -> None:
        """Add a new reference record for this entry."""
        self.references.append(
            {
                self.textindex._ref_type: self.textindex._reference,
                self.start_id: start_id,
                self.suffix: suffix,
                self.locator_emphasis: locator_emphasis,
            }
        )
        if section:
            self.references[-1][self.section_start] = section

    def update_latest_ref_end(
        self,
        end_id: str,
        end_suffix: Optional[str] = None,
        end_section: Optional[str] = None,
    ) -> None:
        """Update the most recent reference's end markers."""
        if not self.references:
            return
        last_ref = self.references[-1]
        last_ref[self.end_id] = end_id
        if end_suffix:
            last_ref[self.end_suffix] = end_suffix
        if end_section:
            last_ref[self.section_end] = end_section

    def depth(self) -> int:
        """Return depth of this entry in the index tree."""
        level, parent = 0, self.parent
        while parent:
            parent = parent.parent
            level += 1
        return level

    def has_children(self) -> bool:
        return bool(self.entries)

    def has_also_refs(self) -> bool:
        """True if entry contains 'also' cross-references."""
        return any(
            ent[self.textindex._ref_type] == self.textindex._also
            for ent in self.cross_references
        )

    def path_list(self) -> List[str]:
        """Return list of ancestor labels leading to this entry."""
        parts, par = [self.label], self.parent
        while par:
            parts.insert(0, par.label)
            par = par.parent
        return parts

    def joined_path(self, path: Optional[List[str]] = None) -> str:
        """Return a stringified joined version of this entry's path."""
        if path is None:
            path = self.path_list()
        return self.textindex._path_delimiter.join(f'"{p}"' for p in path)

    def prefix_search(self, text: str) -> Optional[Self]:
        """Recursive prefix match search starting at this node."""
        if self.label and self.label.startswith(text):
            return self
        for entry in self.entries:
            found = entry.prefix_search(text)
            if found:
                return found
        return None

    def sort_on(self) -> str:
        """Return the lowercase sort key or label text."""
        from .textindex import emphasis  # local import avoids circular refs

        key = self.sort_key if self.sort_key else emphasis(self.label, True)
        return key.lower()

    # ---------------------------------------------------------------------
    # Internal helpers for rendering
    # ---------------------------------------------------------------------
    def _sorted_references(self) -> List[Dict[str, Any]]:
        """Return sorted references respecting emphasis and section mode."""
        refs = list(self.references)
        key_fn = lambda d: d.get(self.locator_emphasis, False)
        if self.textindex.section_mode or self.textindex.sort_emphasis_first:
            refs.sort(key=key_fn, reverse=True)
        return refs

    def _dedupe_section_refs(
        self, refs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """De-duplicate section-mode references (unique start/end pairs)."""
        deduped = []
        seen_pairs = set()
        for ref in refs:
            pair = (ref.get(self.section_start), ref.get(self.section_end))
            if pair not in seen_pairs:
                deduped.append(ref)
                seen_pairs.add(pair)
            else:
                self.textindex.inform(
                    f"Omitting duplicate section reference {ref.get(self.section_start)} "
                    f"for {self.joined_path()}.",
                    force=True,
                )
        return deduped

    def _build_locator_html(self, ref: Dict[str, Any]) -> str:
        """Build an individual locator <a> tag (handles ranges, suffixes, emphasis)."""
        ti = self.textindex
        start_id = ref[self.start_id]
        html = (
            f'<a class="locator" href="#{ti.index_id_prefix}{start_id}" '
            f'data-index-id="{start_id}" data-index-id-elided="{start_id}"></a>'
        )

        # Handle range (start-end)
        has_range = (ti.section_mode and self.section_end in ref) or (
            not ti.section_mode and self.end_id in ref
        )
        if has_range:
            elided = self._elide_end_id(ref)
            end_id = ref[self.end_id]
            html += (
                f"{ti.config.range_separator}"
                f'<a class="locator" href="#{ti.index_id_prefix}{end_id}" '
                f'data-index-id="{end_id}" data-index-id-elided="{elided}"></a>'
            )

        # Add suffixes
        if ref.get(self.suffix):
            html += str(ref[self.suffix])
        if ref.get(self.end_suffix):
            html += " " + str(ref[self.end_suffix])

        # Apply emphasis
        if ref.get(self.locator_emphasis):
            html = f"<em>{html}</em>"

        return html

    def _elide_end_id(self, ref: Dict[str, Any]) -> int:
        """Return elided end ID (e.g. 123–25)."""
        from .textindex import elide_end

        return elide_end(ref[self.start_id], ref[self.end_id])

    def _render_xrefs_of_type(self, ref_type: str) -> str | None:
        """Render all cross-references of a given type as joined HTML."""
        if not self.cross_references:
            return None

        self._sort_cross_refs()
        refs = [
            self._build_xref_html(ref)
            for ref in self.cross_references
            if ref[self.textindex._ref_type] == ref_type
        ]

        return self.textindex.config.list_separator.join(refs) if refs else None

    def _build_xref_html(self, ref: Dict[str, Any]) -> str:
        """Render a single cross-reference entry."""
        path = ref[self.textindex._path]
        path_text = self.textindex.config.path_separator.join(path)
        ref_entry = self.textindex.existing_entry_at_path(path)
        if ref_entry:
            return (
                f'<a class="{self._entry_link_class}" '
                f'href="#{self._entry_id_prefix}{ref_entry.entry_id}">{path_text}</a>'
            )
        self.textindex.inform(
            f"Cross-referenced entry {self.joined_path(path)} doesn't exist "
            f"(in entry {self.joined_path()})",
            severity="warning",
        )
        return path_text

    def _sort_cross_refs(self) -> None:
        """Sort cross-references alphabetically, 'see' before 'also'."""
        if not self.cross_references:
            return
        self.cross_references.sort(
            key=lambda d: "".join(d[self.textindex._path])
        )
        self.cross_references.sort(
            key=lambda d: d[self.textindex._ref_type], reverse=True
        )

    # ---------------------------------------------------------------------
    # Utility / meta
    # ---------------------------------------------------------------------
    def __bool__(self) -> bool:
        return True

    def __len__(self) -> int:
        return 1 + sum(len(c) for c in self.entries)

    def __str__(self) -> str:
        num_children = len(self.entries)
        path_str = self.textindex._path_delimiter.join(self.path_list()[:-1])
        return (
            f'Entry: "{self.label}", depth {self.depth()} '
            f"({'(' + path_str + self.textindex._path_delimiter + ')' if path_str else ''}) "
            f"[{num_children} child{'ren' if num_children != 1 else ''}]"
        )


def string_to_slug(text) -> str:
    """Convert a given string to a slug format.

    Args:
        text (str): The input string to be converted.

    Returns:
        str: A slugified version of the input string.
    """
    # Strip quotes
    text = re.sub(r'[\'"“”‘’]+', "", text)

    # Replace non-alphanumeric characters with whitespace
    text = re.sub(r"\W+", " ", text)

    # Replace whitespace runs with single hyphens
    text = re.sub(r"\s+", "-", text)

    # Remove leading and trailing hyphens
    text = text.strip("-")

    # Return in lowercase
    return text.lower()


class TextIndex:
    """TextIndex is a class designed to index and process document text.
    It facilitates the creation of index entries based on specified patterns,
    supports cross-references, and can output formatted documents with
    integrated indexes.
    """

    # Internal use below.
    _group_headings = False
    _index_id_prefix = "idx"
    _should_run_in = True
    _sort_emphasis_first = False

    # Keys: index placeholder (also vals for cross-references ref-type)
    _also = "also"
    _emphasis_first = "emph-first"
    _headings = "headings"
    _prefix = "prefix"
    _run_in = "run-in"

    # Keys: cross-references
    _path = "path"
    # value for _ref_type key in (non-cross) references
    _reference = "reference"
    _ref_type = "ref-type"

    # Directives
    _also_marker = "+"
    _emphasis_marker = "!"
    _end_marker = "/"
    _inbound_marker = "@"
    _path_delimiter = ">"
    _refs_delimiter = ";"

    # Output
    _disable = "-"
    _enable = "+"
    _range_separator = "–"  # en-dash
    _shared_class = "textindex"

    _alias_prefix = "#"
    _alias_definition_pattern = (
        rf"{_alias_prefix}({_alias_prefix}?[a-zA-Z0-9\-_]+)$"
    )
    _alias_path = "path"
    _alias_token_pattern = (
        rf"(?<!{_alias_prefix}){_alias_prefix}([a-zA-Z0-9\-_]+)"
    )
    _index_directive_pattern = (
        r"(?:(?<!\\)\[([^\]<>]+)(?<!\\)\]"
        r"|([^\s\[\]\{\}<>]++))*(?<!>)\{\^([^\}<\n]*)\}(?!<)"
    )
    _index_placeholder_pattern = r"(?im)^\{index\s*([^\}]*)\s*\}"
    _markdown_heading_pattern = (
        r"^(#{1,6})\s*([^\{]+?)\s*?(?:\{([^\}]*?)\})?\s*$"
    )

    def __init__(
        self, document_text: str, config: IndexConfig | None = None
    ) -> None:
        """Initialize the TextIndex.

        Args:
            document_text (str): document text
            config (IndexConfig): configuration options
        """
        self.config = config or IndexConfig()
        self.entries: list[TextIndexEntry] = []
        self._entry_cache: dict[tuple[str, str | None], TextIndexEntry] = {}
        self.original_document = document_text
        self.intermediate_document = None
        self._index_id_prefix = TextIndex._index_id_prefix
        self._indexed_document = None
        self.verbose = False
        self.aliases = {}
        self.depth = 0  # zero-based greatest depth
        self.section_mode = False

    def apply_config(self, config_string: str) -> None:
        """Type-safe config updater for dataclass IndexConfig."""
        if not config_string:
            return

        valid_keys = {f.name for f in fields(self.config.__class__)}
        import shlex

        for token in shlex.split(config_string):
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            key, value = key.strip(), value.strip().strip("'\"")

            if key in valid_keys:
                field_type = next(
                    f.type
                    for f in fields(self.config.__class__)
                    if f.name == key
                )
                try:
                    value = field_type(value)
                except Exception:
                    pass
                setattr(self.config, key, value)
            elif hasattr(self, "inform"):
                self.inform(
                    f"Unknown config key ignored: {key}", severity="warning"
                )

    def convert_latex_index_commands(self) -> None:
        """Converts LaTeX index commands in the document to index marks.

        This method searches for LaTeX index commands in the document and
        replaces them with corresponding index marks.
        It handles various features such as sorting keys, cross-references, and
        emphasis.
        The converted index marks are added to the intermediate_document
        attribute of the class. If no original document text is available, it
        informs the user with a warning.

        Returns:
            None: This method does not return any value.
        """
        if not self.original_document:
            self.inform(
                "No original document text; can't convert latex commands.",
                severity="warning",
            )
            return

        text = str(self.intermediate_document)
        if not self.intermediate_document:
            text = str(self.original_document)
        offset = 0
        marks_converted = 0

        latex_index_cmd_start = r"\\index\{"
        latex_matches = re.finditer(latex_index_cmd_start, text)
        for lmark in latex_matches:
            # Scan string to find end of \index{…} command, ensuring all braces
            # are balanced.
            quit_after = 150
            braces_open = 1
            idx = lmark.end() + offset
            while (
                braces_open > 0
                and idx < (len(text) - 1)
                and (idx - lmark.end() + offset) < quit_after
            ):
                if text[idx] == "}":
                    braces_open -= 1
                elif text[idx] == "{":
                    braces_open += 1
                idx += 1

            if braces_open != 0:
                # Didn't find end of index command.
                continue

            start, end = lmark.start() + offset, idx
            entire_cmd = text[start:end]
            cmd_content = entire_cmd[len(lmark.group(0)) : -1]

            # Check for continuing locator syntax.
            continuing = False
            cont_match = re.search(r"\|([(\)])$", cmd_content)
            if cont_match:
                if cont_match.group(1) == ")":
                    continuing = True
                cmd_content = cmd_content[: 0 - len(cont_match.group(0))]

            # Deal with emphasis commands, brace-wrapped.
            cmd_content = re.sub(
                r"(?i)\\(?:textbf|textit|textsl|emph)\{([^}]+)}",
                r"_\1_",
                cmd_content,
            )

            # Check for sort key (up to @).
            sort_key = None
            sort_match = re.match(r"([^@]+)@", cmd_content)
            if sort_match:
                sort_key = sort_match.group(1)
                cmd_content = cmd_content[sort_match.end() :]

            # Check for locator emphasis (braceless commands after |).
            loc_emph = False
            loc_emph_match = re.search(
                r"\|(?:textbf|textit|textsl|emph)$", cmd_content
            )
            if loc_emph_match:
                loc_emph = True
                cmd_content = cmd_content[: loc_emph_match.start()]

            # Check for cross-references of both types.
            xref = None
            xref_match = re.search(
                r"\|(see(?:also)?)\s*\{([^}]+)}$", cmd_content
            )
            if xref_match:
                ref_type = xref_match.group(1)
                ref_path = xref_match.group(2)
                path_bits = re.split(r",\s*", ref_path)
                ref_path = ">".join(f'"{elem}"' for elem in path_bits)
                xref = f"{'+' if ref_type == 'seealso' else ''}{ref_path}"
                cmd_content = cmd_content[: xref_match.start()]

            # Deal with hierarchy and quoting in heading.
            heading_parts = cmd_content.split("!")
            heading_path = ">".join(f'"{elem}"' for elem in heading_parts)

            # Construct suitable index mark.
            mark_parts = [heading_path]
            if xref:
                mark_parts.append(f"|{xref}")
            if sort_key:
                mark_parts.append(f'~"{sort_key}"')
            if continuing:
                mark_parts.append("/")
            elif loc_emph:
                mark_parts.append("!")
            mark = f"{{^{' '.join(mark_parts)}}}"
            self.inform(
                f"Converted latex index command:  {entire_cmd}  -->  {mark}"
            )

            # Replace in document, maintaining text-delta offset.
            text = text[:start] + mark + text[end:]
            offset += len(mark) - len(entire_cmd)
            marks_converted += 1

        plural = "" if marks_converted == 1 else "s"
        self.inform(
            (
                f"{marks_converted} latex index command{plural}"
                f" converted to index mark{plural}."
            ),
            force=True,
        )

        self.intermediate_document = text

    def create_index(self, text: str | None = None) -> str:
        """Main entry point to build and insert the text index into document.

        Steps:
            1. Normalize text and prepare for indexing.
            2. Extract index directives.
            3. Parse and process each directive into the index tree.
            4. Render the final index as HTML.
            5. Insert the generated index back into the text.

        Args:
            text(str | None): Text to build and insert index into.

        Returns:
            str: New text with index
        """
        self.inform("Starting index creation...", force=True)

        if text is None:
            text = self.original_document or ""
        doc = self._prepare_document(text)
        directives = self._find_index_directives(doc)

        self.inform(f"Found {len(directives)} index directives", "info")

        for directive in directives:
            self._process_directive(directive)

        index_html = self._render_final_index()
        output_text = self._insert_index_placeholder(doc, index_html)

        self.inform("Index creation complete.", force=True)
        return output_text

    def define_alias(self, name: str, path: str) -> None:
        """Define an alias for a given path in the configuration.

        Args:
            name (str): The name of the alias.
            path (str): The path to be aliased.

        Raises:
            ValueError: If the name is already defined with a different path.

        Returns:
            None
        """
        redefinition = False
        if (
            name in self.aliases
            and self.aliases[name][self._alias_path] != path
        ):
            # Redefinition of existing alias.
            redefinition = True

        self.aliases[name] = {self._alias_path: path}
        mess = "\t"
        if redefinition:
            mess += "Redefined existing alias"
        else:
            mess += "Defined new alias"
        mess += f"'{self._alias_prefix}{name}' as: {self.aliases[name]}"
        self.inform(mess)

    def entry_at_path(
        self, label: str, path_list: List[str], create: bool = True
    ) -> Tuple[TextIndexEntry, bool]:
        """Returns entry named label at path path_list, and whether it already
        existed or not.

        Args:
            label (str): The name of the entry to retrieve.
            path_list (List[str]):
                A list of labels representing the path to the desired entry.
            create (bool, optional):
                If True, creates the entry if it does not exist.
                Defaults to True.

        Returns:
            Tuple[TextIndexEntry, bool]:
                A tuple containing the entry and a boolean indicating whether it
                already existed.
        """
        created = False
        entry = None
        entries = self.entries

        for component in path_list + [label]:
            found_entry = None
            for ent in entries:
                if ent.label == component:
                    found_entry = ent
                    break

            if found_entry:
                entries = found_entry.entries
                entry = found_entry
            else:
                if not create:
                    entry = None
                    self.inform(f"\tFailed to find '{label}'!")
                    break
                mess = f"\tMaking new entry '{component}' (within '"
                mess += entry.label if entry else "at root"

                self.inform(mess + "')")
                new_entry = TextIndexEntry(component, entry)
                new_entry.textindex = self
                entry_depth = new_entry.depth()
                if entry_depth > self.depth:
                    self.depth = entry_depth
                entries.append(new_entry)
                entries = new_entry.entries
                entry = new_entry
                # If we create any entry in the chain, we create all subsequent
                # ones too.
                created = True

        return entry, (entry and not created)

    def existing_entry_at_path(self, path):
        if path:
            path_len = len(path)
            if path_len > 0:
                label = path[-1]
                ancestors = []
                if path_len > 1:
                    ancestors = path[:-1]
                entry, created = self.entry_at_path(label, ancestors, False)
                return entry

        return None

    def find_entry(
        self, label: str, parent: TextIndexEntry | None = None
    ) -> TextIndexEntry | None:
        """Find an existing entry with the given label under the parent.

        Args:
            label: The entry label to search for.
            parent: Parent entry to limit the search scope.
                If None, search top-level entries.

        Returns:
            The matching TextIndexEntry if found, otherwise None.
        """
        key = (label.lower(), parent.label.lower() if parent else None)
        if key in self._entry_cache:
            return self._entry_cache[key]

        search_space = parent.entries if parent else self.entries
        for entry in search_space:
            if entry.label.strip().lower() == label.strip().lower():
                self._entry_cache[key] = entry
                return entry
        return None

    def group_heading(self, letter, is_first=False):
        output = ""
        group_headings = self.group_headings_enabled
        if group_headings or not is_first:
            output += f'\t<dt class="group-separator{" group-heading" if group_headings else ""}">{letter if group_headings else "&nbsp;"}</dt>\n'
        return output

    @property
    def group_headings_enabled(self):
        return self.config.group_headings

    @group_headings_enabled.setter
    def group_headings_enabled(self, val) -> None:
        if isinstance(val, str):
            val = val.lower() == "true"
        elif not isinstance(val, bool):
            val = False
        self.config.group_headings = val
        self._indexed_document = None

    def indexed_document(self):
        if not self._indexed_document:
            self.create_index()
        return self._indexed_document

    def index_html(self, config_string: str | None = None) -> str:
        """Build and render the full index as HTML.

        This method delegates the HTML rendering to HTMLIndexRenderer,
        which recursively generates <ul>/<li> markup for each entry and
        its children.

        Args:
            config_string: Optional configuration override (legacy option).

        Returns:
            A string containing the complete HTML output of the index.
        """
        # Ensure index is built before rendering
        if not getattr(self, "_indexed_document", None):
            self.create_index()

        # Optional: handle legacy or dynamic config updates
        if config_string:
            self.apply_config(config_string)

        # Use the new modular renderer
        renderer = HTMLIndexRenderer(self)
        html_output = renderer.render()

        # Add optional header or wrapper (if config defines one)
        if getattr(self.config, "include_header", False):
            header = getattr(self.config, "header_text", "<h2>Index</h2>")
            html_output = f"{header}\n{html_output}"

        # Add footer if defined
        if getattr(self.config, "include_footer", False):
            footer = getattr(self.config, "footer_text", "")
            html_output = f"{html_output}\n{footer}"

        return html_output

    @property
    def index_id_prefix(self):
        return self._index_id_prefix

    @index_id_prefix.setter
    def index_id_prefix(self, val) -> None:
        self._index_id_prefix = val
        self._indexed_document = None

    def inform(
        self, message: str, severity: str = "normal", force: bool = False
    ) -> None:
        """This method prints an information message to the console with
        optional severity and force flags.

        Args:
            message (str): The message to be printed.
            severity (str, optional):
                The severity level of the message. Defaults to "normal".
            force (bool, optional):
                A flag to override the verbosity setting and always echo the
                message. Defaults to False.

        Returns:
            None: This method does not return any value.
        """
        if not self.config.verbose and not force:
            return
        if severity == "warning" and not self.config.show_warnings:
            return
        print(f"TextIndex [{severity.upper()}]: {message}")

    def load_concordance_file(self, path) -> None:
        """Load a concordance file and process it to add index marks to the
        original document.

        Args:
            path (str): The path to the concordance file.

        Returns:
            None: This method does not return any value.

        Raises:
            IOError: If there is an error opening or reading the file.
        """
        if not self.original_document or self.original_document == "":
            self.inform(
                "No document to index; ignoring concordance file.",
                severity="warning",
            )
            return

        # Load file.
        import os

        conc_contents = None
        concordance = []
        try:
            path = os.path.abspath(os.path.expanduser(path))
            conc_file = open(path, "r")
            conc_contents = conc_file.read()
            conc_file.close()

        except IOError as e:
            self.inform(
                f"Couldn't open concordance file: {e}", severity="error"
            )
            return

        if not conc_contents:
            self.inform(
                f"Couldn't read concordance file: {path}", severity="error"
            )

        # Duplicate original document to work with.
        if self.intermediate_document:
            conc_doc = str(self.intermediate_document)
        else:
            conc_doc = str(self.original_document)

        # Parse into entry-pattern lines.
        for line in conc_contents.split("\n"):
            if line.startswith("#") or re.fullmatch(r"^\s*$", line):
                continue
            # Collapse tab-runs
            line = re.sub(r"\t+", "\t", line)
            # split into columns
            components = line.strip("\n").split("\t")
            if len(components) > 0:
                case_sensitive = False
                if components[0].startswith("\\="):
                    # Since we use = as a prefix for case-sensitive, allow
                    # \= for literal equals by stripping \.
                    components[0] = components[0][1:]
                elif components[0].startswith("="):
                    # Explicitly case-sensitive.
                    components[0] = components[0][1:]
                    case_sensitive = True
                elif components[0] != components[0].lower():
                    # Implicitly case-sensitive because not all-lowercase.
                    case_sensitive = True

                if not case_sensitive:
                    components[0] = "(?i)" + components[0]

                if len(components) == 1:
                    components.append(
                        ""
                    )  # Ensure second column for simplicity.

                concordance.append(
                    components[:2]
                )  # Discard anything after 2nd column.

        # Parse document for TextIndex marks, index directive, and HTML tag
        # ranges to exclude.
        excluded_ranges = []
        excl_pattern = (
            f"{self._index_placeholder_pattern}"
            f"|(?:{self._index_directive_pattern})"
            "|<.*?>"
        )
        excl_matches = re.finditer(excl_pattern, conc_doc)
        for excl in excl_matches:
            excluded_ranges.append([excl.start(), excl.end()])

        # Process concordance entries.
        term_ranges = []
        for conc in concordance:
            # Match and replace this term expression wherever it doesn't
            # intersect excluded ranges.
            term_matches = re.finditer(conc[0], self.original_document)
            new_exclusions = []
            last_checked = 0
            for term in term_matches:
                # Check this isn't an excluded range.
                is_excluded = False
                for i in range(last_checked, len(excluded_ranges)):
                    excl = excluded_ranges[i]
                    start, end = excl[0], excl[1]
                    if end <= term.start():
                        # This excluded range ends before term. Keep looking.
                        last_checked = i
                        continue
                    if start >= term.end():
                        # This excluded range starts after term. We're done.
                        break
                    if term.start() >= start or term.end() <= end:
                        # This excluded range intersects term.
                        # Abort replacement.
                        is_excluded = True
                        break

                if not is_excluded:
                    term_ranges.append(
                        [term.start(), term.end(), term.group(0), conc[1]]
                    )
                    new_exclusions.append([term.start(), term.end()])

            # Exclude found terms for this concordance from future matching.
            excluded_ranges += new_exclusions
            excluded_ranges.sort(key=lambda x: x[0])

        # Sort all term ranges by order of appearance.
        term_ranges.sort(key=lambda x: x[0])

        # Insert suitable index marks.
        offset = 0
        marks_added = 0
        for term in term_ranges:
            mark = f"[{term[2]}]{{^{term[3]}}}"
            conc_doc = (
                conc_doc[: term[0] + offset]
                + mark
                + conc_doc[term[1] + offset :]
            )
            offset += len(mark) - len(term[2])
            marks_added += 1

        # Make the intermediate concorded document available.
        self.intermediate_document = conc_doc

        # Log results.
        self.inform(
            f"Concordance file processed. {len(concordance)} rules generated {marks_added} index marks.",
            force=True,
        )

    def process_wildcards(self, label, text, force_label_only=False):
        if label:
            search_wildcard_pattern = r"\*\^(\-?)"
            replacement = "*"  # fall back on basic wildcard functionality.
            found_item = None
            replace_label = None
            replace_path = None
            found_wildcards = list(re.finditer(search_wildcard_pattern, text))
            if len(found_wildcards) > 0:
                found_item = self.prefix_search(label)
            if found_item:
                replace_label = f'"{found_item.label}"'
                replace_path = self._path_delimiter.join(
                    f'"{elem}"' for elem in found_item.path_list()
                )
            for found_wildcard in reversed(found_wildcards):
                if found_item:
                    label_only = (
                        found_wildcard.group(1) != ""
                    ) or force_label_only
                    if label_only:
                        replacement = replace_label
                    else:
                        replacement = replace_path
                    self.inform(
                        f"\tFound {'(label-only) ' if label_only else ''}prefix match for '{label}': {replacement}"
                    )
                text = (
                    text[: found_wildcard.start()]
                    + replacement
                    + text[found_wildcard.end() :]
                )

            text = text.replace("**", emphasis(label, True).lower())
            text = text.replace("*", emphasis(label, True))

        return text

    def prefix_search(self, text):
        found = None
        for entry in self.entries:
            found = entry.prefix_search(text)
            if found:
                break
        return found

    def render_markdown_heading(
        self, heading_line, extra_attrs_string=None
    ) -> str | None:
        """Renders a Markdown heading as HTML, respecting attribute strings.

        Optional extra attrs will be parsed and incorporated.

        Args:
            heading_line (str):
                The line containing the Markdown heading to render.
            extra_attrs_string (str | None, optional):
                Additional attribute strings for the heading, separated by
                spaces.

        Returns:
            str | None:
                A string representing the rendered HTML heading or
                None if rendering fails.
        """
        # Renders a Markdown heading as HTML, respecting attribute strings.
        # Optional extra attrs will be parsed and incorporated.
        html = ""
        # Renders a Markdown heading as HTML, respecting attribute strings.
        # Optional extra attrs will be parsed and incorporated.

        head_match = re.match(TextIndex._markdown_heading_pattern, heading_line)
        if head_match:
            head_level = len(head_match.group(1))
            title = head_match.group(2).strip()

            tag_id = None
            tag_classes = []
            tag_attrs = {}

            for attr_str in [head_match.group(3), extra_attrs_string]:
                if attr_str:
                    # Parse attribute string like '.class #id key=val'.
                    pattern = re.compile(
                        r'([.#][\w:-]+|[\w:-]+=(?:"[^"]*"|\'[^\']*\'|[^\s]*)|[\w\-.]+)'
                    )
                    for match in pattern.findall(attr_str):
                        item = match
                        if item.startswith(".") and item[1:] not in tag_classes:
                            tag_classes.append(item[1:])
                        elif item.startswith("#"):
                            tag_id = item[1:]
                        elif "=" in item:
                            key, _, val = item.partition("=")
                            val = val or ""
                            this_key = key
                            val = val.strip("\"'")
                            tag_attrs[this_key] = val

            if not tag_id:
                tag_id = string_to_slug(title)

            attrs_html = ""
            if tag_id:
                attrs_html += f' id="{tag_id}"'
            if len(tag_classes) > 0:
                attrs_html += f' class="{" ".join(tag_classes)}"'
            for k, v in tag_attrs.items():
                attrs_html += f' {k}="{v}"'

            return f'<h{head_level}{attrs_html}><a href="#{tag_id}">{title}</a></h{head_level}>'

        return None

    @property
    def should_run_in(self):
        if isinstance(self.textindex.config.run_in_children, bool):
            return self.textindex.config.run_in_children
        return self.textindex.config.run_in_children.lower() == "true"

    @should_run_in.setter
    def should_run_in(self, val) -> None:
        if isinstance(val, str):
            val = val.lower() == "true"
        elif not isinstance(val, bool):
            val = True
        self.textindex.config.run_in_children = val
        self._indexed_document = None

    @property
    def sort_emphasis_first(self) -> bool:
        return self.config.sort_emphasis_first

    @sort_emphasis_first.setter
    def sort_emphasis_first(self, val) -> None:
        if isinstance(val, str):
            val = val.lower() == "true"
        elif not isinstance(val, bool):
            val = True
        self.config.sort_emphasis_first = val
        self._indexed_document = None

    def sort_entries(self, entries):
        from operator import methodcaller

        return sorted(entries, key=methodcaller("sort_on"))

    def _add_entry(self, entry: TextIndexEntry) -> None:
        """Hook for any extra index-entry initialization (cross-refs, etc.)."""
        label_lower = entry.label.lower()

        if label_lower.startswith("see "):
            entry.cross_references.append(
                {
                    "type": self.config.see_label,
                    "target": entry.label[4:].strip(),
                }
            )
        elif label_lower.startswith("see also "):
            entry.cross_references.append(
                {"type": "see_also", "target": entry.label[9:].strip()}
            )
        # Extend here for aliasing, grouping, etc.

    def _alias_replace(self, the_match) -> str:
        """Replace alias with its corresponding path.

        Args:
            the_match (re.Match):
                A match object containing the captured groups of an alias.

        Returns:
            str: The replaced string.
        """
        replacement = the_match.group(0)
        if the_match.group(1) and the_match.group(1) in self.aliases:
            replacement = self._path_delimiter.join(
                f'"{elem}"'
                for elem in self.aliases[the_match.group(1)][
                    TextIndex._alias_path
                ]
            )
        return replacement

    def _find_index_directives(self, text: str) -> list[str]:
        """Extract all index directives from text."""
        patterns = [
            r"{\^index:([^}]+)}",  # Markdown-style
            r"@index\{([^}]+)\}",  # reST-style
            r"\\index\{([^}]+)\}",  # LaTeX-style
        ]
        matches: list[str] = []
        for pattern in patterns:
            matches.extend(re.findall(pattern, text))
        return matches

    def _get_or_create_entry(self, label: str, parent) -> TextIndexEntry:
        """Return existing entry with label under parent or create a new one."""
        existing = self.find_entry(label, parent)
        if existing:
            return existing

        new_entry = TextIndexEntry(label=label, parent=parent, textindex=self)
        if parent:
            parent.entries.append(new_entry)
        else:
            self.entries.append(new_entry)
        return new_entry

    def _index_replace(self, the_match: re.Match) -> str:
        """Replace a match found by `the_match` with its replacement in the HTML
        string.

        This method searches for the text within the first capturing group of
        `the_match` and replaces it with the corresponding text found in the
        output of `self.index_html`.

        Args:
            the_match (re.Match):
                The match object returned by `re.search()` or `re.match()`.
                This object contains information about a successful match,
                including the captured groups.

        Returns:
            str: The modified HTML with the first capturing group replaced.
        """
        return self.index_html(the_match.group(1))

    def _insert_index_placeholder(self, text: str, index_html: str) -> str:
        """Replace the index placeholder or append index HTML at the end."""
        placeholder_pattern = re.compile(r"{\^index}")

        if placeholder_pattern.search(text):
            return placeholder_pattern.sub(index_html, text)

        self.inform(
            "No {^index} placeholder found; appending index at end.", "warning"
        )
        return text.rstrip() + "\n\n" + index_html

    def _parse_index_entry(self, directive: str):
        """Convert a directive string into a TextIndexEntry (hierarchical)."""
        parts = [p.strip() for p in directive.split("!") if p.strip()]
        entry = None
        for label in parts:
            entry = self._get_or_create_entry(label, entry)
        return entry

    def _prepare_document(self, text: str) -> str:
        """Normalize and preprocess the document before indexing."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        if getattr(self, "section_mode", False):
            self.inform(
                "Section mode active: splitting document sections", "info"
            )
            text = self._split_into_sections(text)

        return text

    def _process_directive(self, directive: str) -> None:
        """Process a single index directive and add it to the index tree."""
        try:
            entry = self._parse_index_entry(directive)
            self._add_entry(entry)
        except Exception as exc:
            self.inform(
                f"Failed to process directive '{directive}': {exc}", "warning"
            )

    def _render_final_index(self) -> str:
        """Render the entire index hierarchy into HTML."""
        renderer = HTMLIndexRenderer(self)
        return renderer.render()

    def _split_into_sections(self, text: str) -> str:
        """Split document into sections (stub for section_mode support)."""
        # Placeholder implementation; replace with your section logic.
        return text

    def __bool__(self):
        return True if self._indexed_document else False

    def __len__(self):
        num_entries = 0
        for entry in self.entries:
            num_entries += len(entry)
        return num_entries

    def __str__(self):
        return f"Index ({len(self)} entries)"
