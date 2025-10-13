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

import re
from typing import LiteralString, Self


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


class TextIndexEntry:
    """Provides a data structure for representing entries in a text index.

    Each entry can have labels, references to other entries, and
    cross-references to external resources.

    Attributes:
        entry_id (int): A unique identifier for the entry.
        label (str): The label for the entry.
        parent (TextIndexEntry): The parent entry to which this entry belongs.
        entries (list[TextIndexEntry]): The list of child entries.
        references (list[dict]):
            List of references to other entries, stored as dictionaries with
            keys indicating reference types and their values.
        cross_references (list[dict]):
            List of cross-references related to the entry.
        sort_key (any): The key used for sorting the entry in a text index.
        textindex (TextIndex):
            The associated TextIndex instance that contains this entry.

    Methods:
        sort_on() -> LiteralString:
            Provides a method to retrieve the sorting key or label, converted
            to lowercase.
        add_reference(
            start_id, suffix=None, locator_emphasis=False, section=None
        ): Adds a reference to another entry with optional parameters for start
            and end IDs, suffixes, locator emphasis, and sections.
        add_cross_reference(ref_type, path):
            Adds a cross-reference to an external resource.
        update_latest_ref_end(
            end_id, end_suffix=None, end_section=None
        ): Updates the latest reference's end information.
        depth() -> int:
            Returns the depth of the entry in the text index hierarchy.
        has_children() -> bool: Checks if the entry has any child entries.
        has_also_refs() -> bool:
            Checks if the entry has cross-references to resources marked as
            'also'.
        run_in_children() -> bool:
            Determines if this entry should be rendered its children in run-in
            style, based on its depth relative to other entries.
        prefix_search(text) -> TextIndexEntry:
            Searches for an entry with a given label prefix.
        path_list() -> list[str]:
            Returns the path from the root entry to the current entry as a list
            of labels.
        joined_path(path=None) -> str:
            Joins the path elements into a string with appropriate delimiters
            and quotes.
        render_references():
            Renders the references for the entry, considering emphasis-first
            sorting and section mode.

    Note:
        The class uses internal attributes prefixed with underscores (`_`) to
        store information that is not intended for public use.
        These attributes are managed internally by the TextIndexEntry class and
        should not be accessed or modified directly.
    """

    # Keys for dicts in instances' self.references list.
    _entry_id_prefix = "entry"
    _entry_link_class = "entry-link"
    _next_id = 0
    end_id = "end-id"
    end_suffix = "end-suffix"
    locator_emphasis = "locator-emphasis"
    section_end = "start-end"
    section_start = "start-section"
    start_id = "start-id"
    suffix = "suffix"

    def __init__(self, label: str = None, parent: Self = None) -> None:
        """Initializes a new instance of the TextIndexEntry class.

        Args:
            label (str): The label for the entry.
            parent (TextIndexEntry):
                The parent entry to which this entry belongs.

        Returns:
            None: This method does not return any value.
        """
        self.entry_id = TextIndexEntry._next_id
        TextIndexEntry._next_id += 1

        self.label = label
        self.parent = parent
        self.entries: list[Self] = []  # children
        self.references = []  # list of dicts; see keys above.
        self.cross_references = []
        self.sort_key = None
        self.textindex = None

    def add_cross_reference(self, ref_type, path) -> None:
        """Adds a cross-reference to the list of references if it does not
        already exist.

        Args:
            ref_type (str): The type of reference to be added.
            path (str): The path associated with the reference.

        Returns:
            None: This method does not return any value.
        """
        # Check this isn't a duplicate.
        if len(self.cross_references) > 0:
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
        suffix: str = None,
        locator_emphasis: bool = False,
        section: str = None,
    ) -> None:
        """Adds a reference to the collection of references.

        Args:
            start_id (str): The starting identifier for the reference.
            suffix (str, optional):
                A suffix to be added to the reference. Defaults to None.
            locator_emphasis (bool, optional):
                A boolean indicating if emphasis should be applied to the
                locator. Defaults to False.
            section (str, optional):
                The section to which this reference belongs. Defaults to None.

        Returns:
            None: This method does not return any value.
        """
        self.references.append(
            {
                TextIndex._ref_type: TextIndex._reference,
                self.start_id: start_id,
                self.suffix: suffix,
                self.locator_emphasis: locator_emphasis,
            }
        )
        if section:
            self.references[-1][self.section_start] = section

    def depth(self) -> int:
        """Returns the depth of the current node in the tree.

        The depth of a node is defined as the number of edges on the longest
        path from the node to a leaf node.
        In other words, it's one more than the height of the subtree rooted at
        that node.

        Returns:
            int: The depth of the current node.
        """
        level = 0
        par = self.parent
        while par:
            par = par.parent
            level += 1
        return level

    def has_children(self) -> bool:
        """Checks if the current node has any children.

        Returns:
            bool: True if there are child entries, False otherwise.
        """
        return len(self.entries) > 0

    def has_also_refs(self) -> bool:
        """Determines if the document contains references of type 'also'.

        This method checks the list of cross-references for any entries where
        the reference type is 'also'.
        If such a reference is found, it returns True; otherwise,
        it returns False.

        Returns:
            bool: A boolean value indicating whether there are references of
            type 'also'.
        """
        also_xrefs = False
        if len(self.cross_references) > 0:
            for ent in self.cross_references:
                if ent[TextIndex._ref_type] == TextIndex._also:
                    also_xrefs = True
                    break
        return also_xrefs

    def joined_path(self, path=None):
        """Returns a string representation of the joined path.

        Args:
            path (list or None):
                The list of path elements.
                Defaults to using the self.path_list() method if not provided.

        Returns:
            str:
                A string with each path element wrapped in double quotes and
                joined by the textindex._path_delimiter.
        """
        if path is None:
            path = self.path_list()
        return self.textindex._path_delimiter.join(f'"{elem}"' for elem in path)

    def path_list(self):
        """Constructs a path to the current node by traversing its parent nodes
        until it reaches the root node.

        It collects all the labels in a list, starting from the current node and
        moving upwards through its ancestors.

        Returns:
            list[str]:
                Returns a list of the labels from the top to bottom hierarchy.
        """
        components = [self.label]
        par = self.parent
        while par:
            components.insert(0, par.label)
            par = par.parent
        return components

    def prefix_search(self, text: str) -> Self | None:
        """Searches for a prefix in the tree structure starting from the current
        node.

        Args:
            text (str): The prefix to search for within the tree.

        Returns:
            Self | None: The node with matching prefix if found, else None.
        """
        found = None
        if self.label.startswith(text):
            return self
        for entry in self.entries:
            if found := entry.prefix_search(text):
                break
        return found

    def render_references(self):
        """Render reference locators based on the current state of
        self.references.

        This method generates HTML links for each locator in self.references.
        The locators are sorted and formatted according to various conditions:
        - Section mode prioritizes emphasis.
        - Emphasis-first sorting is applied if not in section mode.
        - A limit of 10 references is enforced to prevent excessive clutter.
        - Locators are wrapped in <a> tags with appropriate classes and data
          attributes for linking.

        Returns:
            str: A string containing the formatted locators as a field-separated
                 list, or None if no references exist.
        """
        refs = []

        if len(self.references) > 0:
            the_refs = self.references

            # Handle section mode; de-duplicate sections (some may be continuing), prioritising emphasis.
            if self.textindex.section_mode:
                # Sort emphasised first.
                the_refs = sorted(
                    the_refs,
                    key=lambda d: d[TextIndexEntry.locator_emphasis],
                    reverse=True,
                )
                # Treat continuing locators with same start and end section as separate locators for de-duplication.
                for this in the_refs:
                    if (
                        TextIndexEntry.section_end in this
                        and this[TextIndexEntry.section_end]
                        == this[TextIndexEntry.section_start]
                    ):
                        this.pop(TextIndexEntry.section_end)
                deduped = []
                for this in the_refs:
                    # Use reference if it doesn't have an exact (section start and end) match already.
                    sec_tuples = [
                        [
                            i.get(f)
                            for f in [
                                TextIndexEntry.section_start,
                                TextIndexEntry.section_end,
                            ]
                        ]
                        for i in deduped
                    ]
                    this_tuple = [
                        this.get(TextIndexEntry.section_start),
                        this.get(TextIndexEntry.section_end),
                    ]
                    if this_tuple not in sec_tuples:
                        deduped.append(this)
                    else:
                        self.textindex.inform(
                            f"Omitting duplicate section reference {this[TextIndexEntry.section_start]} for {self.joined_path()}.",
                            force=True,
                        )
                the_refs = deduped
                if not self.textindex.sort_emphasis_first:
                    deduped = sorted(
                        deduped, key=lambda d: d[TextIndexEntry.start_id]
                    )

            # Respect emphasis-first option.
            if (
                self.textindex.sort_emphasis_first
                and not self.textindex.section_mode
            ):
                the_refs = sorted(
                    the_refs,
                    key=lambda d: d[TextIndexEntry.locator_emphasis],
                    reverse=True,
                )

            ref_limit = 10
            if len(the_refs) >= ref_limit:
                self.textindex.inform(
                    f"Entry {self.joined_path()} has {len(the_refs)} locators. Consider reorganising or being more selective.",
                    severity="warning",
                )

            loc_class = "locator"
            for i in range(len(the_refs)):
                ref = the_refs[i]
                sec_start = (
                    f' data-section="{ref[TextIndexEntry.section_start]}"'
                    if TextIndexEntry.section_start in ref
                    else ""
                )
                locator_html = f'<a class="{loc_class}" href="#{self.textindex.index_id_prefix}{ref[TextIndexEntry.start_id]}" data-index-id="{ref[TextIndexEntry.start_id]}" data-index-id-elided="{ref[TextIndexEntry.start_id]}"{sec_start}></a>'
                if (
                    self.textindex.section_mode
                    and TextIndexEntry.section_end in ref
                ) or (
                    not self.textindex.section_mode
                    and TextIndexEntry.end_id in ref
                ):
                    elided_end = elide_end(
                        ref[TextIndexEntry.start_id], ref[TextIndexEntry.end_id]
                    )
                    sec_end = (
                        f' data-section="{ref[TextIndexEntry.section_end]}"'
                        if TextIndexEntry.section_end in ref
                        else ""
                    )
                    locator_html += TextIndex._range_separator
                    locator_html += f'<a class="{loc_class}" href="#{self.textindex.index_id_prefix}{ref[TextIndexEntry.end_id]}" data-index-id="{ref[TextIndexEntry.end_id]}" data-index-id-elided="{elided_end}"{sec_end}></a>'
                suffix_applied = False
                if TextIndexEntry.suffix in ref and ref[TextIndexEntry.suffix]:
                    locator_html += f"{ref[TextIndexEntry.suffix]}"
                    suffix_applied = True
                if (
                    TextIndexEntry.end_suffix in ref
                    and ref[TextIndexEntry.end_suffix]
                ):
                    locator_html += f"{' ' if suffix_applied else ''}{ref[TextIndexEntry.end_suffix]}"
                if ref[TextIndexEntry.locator_emphasis]:
                    locator_html = f"<em>{locator_html}</em>"

                refs.append(locator_html)

            if len(refs) > 0:
                return TextIndex._field_separator.join(refs)

        return None

    def render_also_references(self) -> str | None:
        """Render also-type cross-references.

        Returns:
            str | None: The rendered string containing the also-type
                cross-references, or None if no such references exist.
        """
        # Also-type cross-references.
        return self.render_xrefs_of_type(TextIndex._also)

    def render_cross_references(self) -> str | None:
        """Render see-type cross-references.

        This method generates a list of cross-reference entries for the 'see'
        type from the text index. The 'see' type typically indicates that an
        item is related to another item in some way, such as a glossary entry or
        a reference.

        The method returns a list of cross-reference entries, where each entry
        contains:
        - The label (or title) associated with the see-type reference.
        - The URL or identifier pointing to the target item.

        For example:
        [
            {
                "label": "Glossary Entry",
                "url": "https://example.com/glossary-entry"
            },
            {
                "label": "Related Topic",
                "url": "https://example.com/topic"
            }
        ]
        """
        # See-type cross-references.
        return self.render_xrefs_of_type(TextIndex.see)

    def render_xrefs_of_type(self, ref_type=TextIndex.see):
        """ """
        # Render cross-references.
        refs = []

        if len(self.cross_references) > 0:
            self.sort_cross_refs()

            for i in range(len(self.cross_references)):
                ref = self.cross_references[i]
                if ref[TextIndex._ref_type] == ref_type:
                    ref_path = ref[TextIndex._path]
                    ref_entry = self.textindex.existing_entry_at_path(ref_path)
                    refs.append(f"{TextIndex._path_separator.join(ref_path)}")
                    if ref_entry:
                        refs[-1] = (
                            f'<a class="{TextIndexEntry._entry_link_class}" href="#{TextIndexEntry._entry_id_prefix}{ref_entry.entry_id}">{refs[-1]}</a>'
                        )
                    else:
                        self.textindex.inform(
                            f"Cross-referenced entry {self.joined_path(ref_path)} doesn't exist (in entry {self.joined_path()})",
                            severity="warning",
                        )
            if len(refs) > 0:
                return f"{TextIndex._refs_delimiter} ".join(refs)

        return None

    def run_in_children(self) -> bool:
        """Determines if this entry should be rendered in run-in style.

        The function checks whether the current entry should be formatted as a
        run-in element.
        Top-level entries are at level 0, and are considered children of the
        index itself.
        Depths 0 and 1 (top-level entries, and their sub-entries) are always
        indented.
        Thereafter, for practical reasons, only the deepest level is run-in.
        A run-in element is typically used to display entries that are closely
        related or part of a group.

        Notes:
            Please don't make indexes deeper than root+2 levels though, for your
            readers' sake!


        Parameters:
            self (Entry):
                The Entry instance for which to determine run-in status.

        Returns:
            bool: True if the entry should be rendered in run-in style,
                False otherwise.
        """
        if self.textindex.should_run_in:
            my_depth = self.depth()
            return my_depth > 0 and my_depth == self.textindex.depth - 1
        return False

    def sort_cross_refs(self) -> None:
        """Sorts the cross-references in this object.

        The sorting process involves two main steps:

        1. **Sort by Path Alphabetically**:
           - The `cross_references` list is sorted based on the concatenated
             path of each reference.
           - This ensures that paths are compared lexicographically, meaning
             they are ordered alphabetically.

        2. **Sort See-Refs First**:
           - After sorting the cross-references alphabetically by their paths,
             see-references (those with a specific ref_type) are sorted first.
           - The sorting order for see-references is reversed, meaning they
             appear at the end of the list instead of at the beginning.

        This method modifies the `cross_references` attribute in place and does
        not return any value.

        Returns:
            None: This method does not return any value.
        """
        if len(self.cross_references) > 0:
            # First sort by path alphabetically.
            self.cross_references.sort(
                key=lambda d: "".join(d[TextIndex._path])
            )
            # Then sort the see-refs first.
            self.cross_references.sort(
                key=lambda d: d[TextIndex._ref_type], reverse=True
            )

    def sort_on(self) -> LiteralString:
        """Provides a method to retrieve the sorting key or label, converted to
        lowercase.

        Summary:
            The `sort_on` method is designed to provide a consistent way of
            accessing and normalizing the sorting key for an object.
            It returns either the stored `sort_key` attribute if it exists, or
            the label converted to lowercase using the `emphasis` function.

        Returns:
            LiteralString: The sorting key or label if it exists.
        """
        return (
            self.sort_key if self.sort_key else emphasis(self.label, True)
        ).lower()

    def update_latest_ref_end(
        self, end_id: str, end_suffix: str = None, end_section: str = None
    ) -> None:
        """Updates the latest reference's fields with new values.

        Args:
            end_id (str): The identifier of the end point.
            end_suffix (str, optional):
                The suffix associated with the end point. Defaults to None.
            end_section (str, optional):
                The section or group associated with the end point.
                Defaults to None.

        Returns:
            None: This method does not return any value.
        """
        self.references[-1][self.end_id] = end_id
        if end_suffix:
            self.references[-1][self.end_suffix] = end_suffix
        if end_section:
            self.references[-1][self.section_end] = end_section

    def __bool__(self):
        return True

    def __len__(self):
        num_entries = 1
        for entry in self.entries:
            num_entries += len(entry)
        return num_entries

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        num_children = len(self.entries)
        path_str = TextIndex._path_delimiter.join(self.path_list()[:-1])
        return f'Entry: "{self.label}", depth {self.depth()} {"(" + path_str + TextIndex._path_delimiter + ")" if path_str != "" else ""} [{num_children} child{"" if num_children == 1 else "ren"}{", run-in" if self.run_in_children() else ", indented"}]'


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
    _see_also_label = "see also"
    _see_label = "see"
    _should_run_in = True
    _sort_emphasis_first = False

    # Keys: index placeholder (also vals for cross-references ref-type)
    _also = "also"
    _emphasis_first = "emph-first"
    _headings = "headings"
    _prefix = "prefix"
    _run_in = "run-in"
    _see = "see"

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
    _category_separator = ". "
    _disable = "-"
    _enable = "+"
    _field_separator = ", "
    _list_separator = "; "
    _path_separator = ": "
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

    def __init__(self, document_text: str | None = None) -> None:
        """Initialize the TextIndex.

        Args:
            document_text (str): document text.
        """
        self.original_document = document_text
        self.intermediate_document = None
        self.entries = []
        self._see_label = TextIndex._see_label
        self._see_also_label = TextIndex._see_also_label
        self._index_id_prefix = TextIndex._index_id_prefix
        self._group_headings = TextIndex._group_headings
        self._should_run_in = TextIndex._should_run_in
        self._sort_emphasis_first = TextIndex._sort_emphasis_first
        self._indexed_document = None
        self.verbose = False
        self.aliases = {}
        self.depth = 0  # zero-based greatest depth
        self.section_mode = False

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

    def create_index(self) -> None:
        """ """
        entry_number = 0
        if self.original_document:
            indexed_doc = f"{self.intermediate_document if self.intermediate_document else self.original_document}"
            self.aliases = {}

            # Determine mode.
            idx_placeholders = re.finditer(
                TextIndex._index_placeholder_pattern, indexed_doc
            )
            for placeholder in idx_placeholders:
                if re.search(r"\bsection\b", placeholder.group(0)):
                    self.section_mode = True
                    self.inform(
                        "Section mode enabled for all index directives in document.",
                        force=True,
                    )
                    break

            # Find all directives.
            offset = 0  # accounting for replacements
            last_mark_end = 0
            enabled = True
            section_number = None
            section_stack = []
            prev_heading_level = 1
            directive_matches = re.finditer(
                TextIndex._index_directive_pattern, indexed_doc
            )
            for directive in directive_matches:
                if self.section_mode:
                    # Handle intervening headings.
                    headings = re.finditer(
                        TextIndex._markdown_heading_pattern,
                        indexed_doc[last_mark_end : directive.start() + offset],
                        re.MULTILINE,
                    )
                    if headings:
                        num_heads = 0
                        delta = 0
                        for head_match in headings:
                            hashes, title, attr_str = (
                                head_match.group(1),
                                head_match.group(2),
                                head_match.group(3),
                            )
                            head_level = len(hashes)
                            title = title.strip()

                            increment_section = True
                            if attr_str and re.search(
                                r"(?i)\.(no-?toc|unlisted)\b", attr_str
                            ):
                                increment_section = False

                            if len(section_stack) == 0:
                                # Treat the first heading as root level, even if
                                # not h1.
                                prev_heading_level = head_level
                                section_stack.append(0)
                            if increment_section:
                                if head_level == prev_heading_level:
                                    section_stack[-1] += 1
                                elif head_level > prev_heading_level:
                                    for x in range(
                                        prev_heading_level, head_level - 1
                                    ):
                                        section_stack.append(0)
                                    section_stack.append(1)
                                else:
                                    for x in range(
                                        head_level, prev_heading_level
                                    ):
                                        section_stack.pop()
                                    section_stack[-1] += 1
                                prev_heading_level = head_level

                            # Format section number for use as an attribute in
                            # headings and index locators.
                            section_number = ".".join(
                                str(i) for i in section_stack
                            )

                            # Apply section number to its heading, by rendering
                            # the Markdown heading as HTML, preserving braced
                            # attributes.
                            markdown_heading = head_match.group(0)
                            html_heading = (
                                self.render_markdown_heading(
                                    markdown_heading,
                                    f'.heading-section data-section="{section_number}"'
                                    if increment_section
                                    else None,
                                )
                                + "\n"
                            )
                            # print(f"Encountered heading: {markdown_heading}\n
                            # \tSection is: {section_number}\n\tWould rewrite
                            # as: {html_heading}")

                            # Perform heading replacement in the document.
                            start = last_mark_end + head_match.start() + delta
                            end = last_mark_end + head_match.end() + delta
                            # segment = indexed_doc[start:end]
                            indexed_doc = (
                                indexed_doc[:start]
                                + html_heading
                                + indexed_doc[end:]
                            )
                            delta += len(html_heading) - len(markdown_heading)
                            num_heads += 1

                        offset += delta
                        last_mark_end = directive.start() + offset

                # Parse and encapsulate each entry, either as an object or a
                # range-end.
                self.inform(f"Directive found: {directive.group(0)}")

                params = directive.group(3).strip()
                closing = False
                emphasis = False
                sort_key = None
                suffix = None
                cross_references = []

                # Determine type of directive.
                toggling_directive = (
                    params == TextIndex._enable or params == TextIndex._disable
                )
                status_toggled = False
                if params.endswith(self._end_marker):
                    closing = True
                    params = params[: -len(self._end_marker)]
                    self.inform("\tClosing mark: /")
                elif params.endswith(self._emphasis_marker):
                    emphasis = True
                    params = params[: -len(self._emphasis_marker)]
                    self.inform("\tLocator Emphasis: !")
                elif params == TextIndex._enable and not enabled:
                    enabled = True
                    self.inform(
                        "============ Processing enabled.  ============"
                    )
                    status_toggled = True
                elif params == TextIndex._disable and enabled:
                    enabled = False
                    self.inform(
                        "============ Processing disabled. ============"
                    )
                    status_toggled = True

                if toggling_directive and (enabled or status_toggled):
                    # This was a toggling mark, and we're either now enabled or we were when we encountered it.
                    # Remove the mark.
                    indexed_doc = (
                        indexed_doc[: directive.start() + offset]
                        + indexed_doc[directive.end() + offset :]
                    )
                    delta = 0 - len(directive.group(0))
                    offset += delta

                if not enabled or status_toggled or toggling_directive:
                    continue

                # Determine label path.
                label = None
                label_path_components = []
                if directive.group(1):  # leading bracketed span
                    label = directive.group(1)
                elif directive.group(2):  # leading implicit non-whitespace span
                    label = directive.group(2)
                span_contents = label  # for replacement

                # Still need to check for a label path within the directive.
                label_match = re.match(r"^([^\|\[~]+)", params)
                if label_match:
                    label_match_text = label_match.group(0).strip()

                    # Process aliases before splitting path.
                    if len(self.aliases) > 0 and len(label_match_text) > 0:
                        label_match_text = re.sub(
                            TextIndex._alias_token_pattern,
                            self._alias_replace,
                            label_match_text,
                        )

                    # Handle wildcards in label path.
                    label_match_text = self.process_wildcards(
                        label, label_match_text
                    )

                    # Split label path.
                    label_path_components = label_match_text.split(
                        self._path_delimiter
                    )

                    # Having already replaced alias references, check for alias definition at end of label path.
                    alias_definition_match = re.search(
                        TextIndex._alias_definition_pattern,
                        label_path_components[-1],
                    )
                    if alias_definition_match:
                        label_path_components[-1] = label_path_components[-1][
                            : alias_definition_match.start()
                        ]

                    # Remove quotes from path elements.
                    label_path_components = [
                        component.strip("'\"")
                        for component in label_path_components
                    ]

                    last_component = label_path_components[-1]
                    if (
                        last_component != self._path_delimiter
                        and last_component != ""
                    ):
                        label = last_component
                        label_path_components.pop()  # remove last item, which
                        # is now the label.
                    if (
                        len(label_path_components) > 0
                        and label_path_components[-1] == ""
                    ):
                        label_path_components.pop()  # remove empty last item.

                    # Trim label path from params.
                    params = (
                        params[: label_match.start()]
                        + params[label_match.end() :]
                    )

                    # Check for alias definition.
                    alias_without_reference = False
                    if alias_definition_match:
                        alias_name = alias_definition_match.group(1)
                        if alias_name.startswith(TextIndex._alias_prefix):
                            alias_without_reference = True
                            alias_name = alias_name.lstrip(
                                TextIndex._alias_prefix
                            )

                        if alias_definition_match.start() > 0:
                            # Alias definition at end of an internally-specified
                            # label.
                            # Trim alias portion from label, and define.
                            self.define_alias(
                                alias_name, label_path_components + [label]
                            )
                        else:
                            # Alias found at start of label. Either an alias
                            # reference, or a definition without an internal
                            # label (foo>#bar or just #bar).
                            if len(label_path_components) == 0:
                                # No path components. Could be an alias
                                # definition at root, or an alias reference.
                                # Try to load the alias.
                                if alias_name in self.aliases:
                                    # It's a valid alias reference. Load alias.
                                    label = self.aliases[alias_name][
                                        alias_label
                                    ]
                                    label_path_components = self.aliases[
                                        alias_name
                                    ][TextIndex._alias_path]
                                    self.inform(
                                        f"\tLoaded alias {self.aliases[alias_name]} for directive: {directive.group(0)}"
                                    )
                                else:
                                    # No path components, and an alias reference to a non-existent alias. Define a new alias instead.
                                    if span_contents and len(span_contents) > 0:
                                        label = span_contents
                                        self.define_alias(
                                            alias_name,
                                            label_path_components + [label],
                                        )
                            else:
                                # Path components exist, so this is an alias definition without an internal label.
                                if span_contents and len(span_contents) > 0:
                                    # We already had a label from either a bracketed span, or implicitly. Define alias.
                                    label = span_contents
                                    self.define_alias(
                                        alias_name,
                                        label_path_components + [label],
                                    )
                                else:
                                    # No label specified either internally or previously; can't define an alias.
                                    label = None
                                    self.inform(
                                        f"Alias definition without a label: {directive.group(0)}",
                                        severity="warning",
                                    )

                        if alias_without_reference:
                            if label:
                                self.inform(
                                    f"\tUnreferenced alias created; skipping rest of directive: {directive.group(0)}"
                                )
                            else:
                                self.inform(
                                    f"\tUnreferenced alias definition without a label; skipping rest of directive: {directive.group(0)}",
                                    severity="warning",
                                )

                            # Replace directive in indexed_document.
                            span_html = f"{emphasis(span_contents) if span_contents else ''}"
                            indexed_doc = (
                                indexed_doc[: directive.start() + offset]
                                + span_html
                                + indexed_doc[directive.end() + offset :]
                            )
                            delta = len(span_html) - len(directive.group(0))
                            offset += delta
                            continue

                self.inform(f"\tLabel: {label}")
                if len(label_path_components) > 0:
                    self.inform(f"\tPath: {label_path_components}")

                if not label:
                    self.inform(
                        f"No entry label specified in directive. Ignoring: {directive.group(0)}",
                        severity="warning",
                    )
                    continue

                # Suffix.
                params = params.strip()
                suffix_match = re.search(r"\s*\[([^\]]+)(?<!\\)\]\s*", params)
                if suffix_match:
                    suffix = suffix_match.group(1)
                    params = (
                        params[: suffix_match.start()]
                        + params[suffix_match.end() :]
                    )
                    self.inform(f"\tSuffix: {suffix}")

                # Sort key.
                params = params.strip()
                sort_match = re.search(r"\s*\~(['\"]?)(.+)\1$", params)
                if sort_match:
                    sort_key = sort_match.group(2)

                    # Handle wildcards in sort key.
                    sort_key = self.process_wildcards(
                        span_contents, sort_key, True
                    )

                    self.inform(f"\tSort as: {sort_key}")
                    params = (
                        params[: sort_match.start()]
                        + params[sort_match.end() :]
                    )

                # Cross-references.
                cross_match = re.match(r"\|(.+)$", params)
                create_ref = True
                if cross_match:
                    refs_string = cross_match.group(1).strip()

                    # Process aliases before splitting path.
                    if len(self.aliases) > 0 and len(refs_string) > 0:
                        refs_string = re.sub(
                            TextIndex._alias_token_pattern,
                            self._alias_replace,
                            refs_string,
                        )

                    # Handle wildcards in cross-refs.
                    refs_string = self.process_wildcards(
                        span_contents, refs_string
                    )

                    refs = refs_string.split(self._refs_delimiter)
                    for ref in refs:
                        inbound = False
                        ref_type = self.see
                        ref = ref.strip()

                        if ref.startswith(self._inbound_marker):
                            inbound = True
                            ref = ref[len(self._inbound_marker) :]

                        if ref.startswith(self._also_marker):
                            ref_type = self._also
                            ref = ref[len(self._also_marker) :]
                        elif not inbound:
                            # Don't create a (page-)reference for this mark's entry if there's a (non-also) cross-reference.
                            create_ref = False

                        ref_path_components = ref.split(self._path_delimiter)
                        ref_path_components = [
                            component.strip("'\"")
                            for component in ref_path_components
                        ]

                        if inbound:
                            # Cross-ref in different entry, referencing this mark's entry. Find other entry.
                            source_label = ref_path_components[-1]
                            source_path_components = []
                            if len(ref_path_components) > 1:
                                source_path_components = ref_path_components[
                                    :-1
                                ]
                            source_entry, existed = self.entry_at_path(
                                source_label, source_path_components, True
                            )
                            self.inform(
                                f"\tCreating inbound '{ref_type}' cross-reference from entry '{source_label}' {'(Path: ' + source_path_components + ')' if len(ref_path_components) > 1 else '(at root)'}"
                            )
                            source_entry.add_cross_reference(
                                ref_type, label_path_components + [label]
                            )

                        else:
                            # Cross-ref within this mark's entry.
                            cross_references.append(
                                {
                                    self._ref_type: ref_type,
                                    self._path: ref_path_components,
                                }
                            )

                    params = (
                        params[: cross_match.start()]
                        + params[cross_match.end() :]
                    )
                    if len(cross_references) > 0:
                        self.inform(f"\tCross-refs: {cross_references}")

                if len(params.strip()) > 0:
                    self.inform(
                        f"*** Unparsed directive content: '{params}' (please report this!) ***",
                        severity="warning",
                    )

                # Prepare next reference id.
                entry_number += 1

                # Insert into entries tree.
                entry, existed = self.entry_at_path(
                    label, label_path_components, not closing
                )
                display_entry_path = f" {self._path_delimiter} ".join(
                    label_path_components + [label]
                )
                if not entry and closing:
                    # Entry doesn't exist, but we're trying to end its (non-existent) range.
                    self.inform(
                        f'Attempted to close non-existent entry "{display_entry_path}". Ignoring: {directive.group(0)}',
                        severity="warning",
                    )
                    continue
                if entry and closing:
                    # Entry exists, and we're closing its range. If it already has a closing ID, update it.
                    if len(entry.references) > 0:
                        if TextIndexEntry.end_id in entry.references[-1]:
                            self.inform(
                                f'Altering existing end-location of range for reference "{display_entry_path}": {directive.group(0)}',
                                severity="warning",
                            )
                        entry.update_latest_ref_end(
                            entry_number, suffix, section_number
                        )
                        self.inform(
                            f'\tSet end-location for reference to "{display_entry_path}".'
                        )
                    else:
                        # Entry exists, but has no references, so we can't set an end id.
                        self.inform(
                            f'Attempted to close non-existent reference for existing entry "{display_entry_path}". Ignoring: {directive.group(0)}',
                            severity="warning",
                        )
                else:
                    # We now have the correct entry, whether it existed before or not. Populate.
                    if create_ref:
                        entry.add_reference(
                            entry_number, suffix, emphasis, section_number
                        )
                    elif suffix or emphasis:
                        self.inform(
                            f"Ignoring suffix/emphasis in cross-reference: {directive.group(0)}",
                            severity="warning",
                        )

                    if sort_key:
                        if entry.sort_key and entry.sort_key != sort_key:
                            self.inform(
                                f"Altering existing sort-key for reference \"{display_entry_path}\" (was '{entry.sort_key}', now '{sort_key}'). Directive was: {directive.group(0)}",
                                severity="warning",
                            )
                        entry.sort_key = sort_key
                    if len(cross_references) > 0:
                        for ref in cross_references:
                            entry.add_cross_reference(
                                ref[self._ref_type], ref[self._path]
                            )
                        if existed:
                            self.inform(
                                f"\tAdded cross-references to existing entry '{label}'"
                            )

                # Replace directive in indexed_document with suitable span.
                span_html = f'<span id="{self.index_id_prefix}{entry_number}" class="{TextIndex._shared_class}">{emphasis(span_contents) if span_contents else ""}</span>'
                indexed_doc = (
                    indexed_doc[: directive.start() + offset]
                    + span_html
                    + indexed_doc[directive.end() + offset :]
                )
                delta = len(span_html) - len(directive.group(0))
                offset += delta
                last_mark_end = directive.end() + offset

            self.inform(f"{len(self)} entries created.", force=True)

            # Replace each index placeholder with a suitable HTML index.
            self._indexed_document = indexed_doc  # needs an initial value otherwise index_html() will recurse.
            indexed_doc = re.sub(
                TextIndex._index_placeholder_pattern,
                self._index_replace,
                indexed_doc,
            )

        self._indexed_document = indexed_doc

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

    def entry_at_path(self, label, path_list, create=True):
        """ """
        # Returns entry named label at path path_list, and whether it already
        # existed or not.
        # If entry doesn't exist and create is True, creates it; else returns
        # None.

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
                self.inform(
                    f"\tMaking new entry '{component}' ({"within '" + entry.label + "'" if entry else 'at root'})"
                )
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

    def entry_html(self, entry: TextIndexEntry) -> str:
        # Cross-refs (non-also), then ordered references, then parent's
        # also-refs.
        refs_html = ""
        refs_output = False
        running_in = entry.parent and entry.parent.run_in_children()

        # Entry's see-references.
        has_xrefs = False
        xrefs_html = entry.render_cross_references()
        if xrefs_html is not None:
            if running_in:
                refs_html += (
                    f" (<em>{self.see_label.lower()}</em> {xrefs_html})"
                )
            else:
                refs_html += (
                    f"{TextIndex._category_separator}<em>"
                    f"{self.see_label.capitalize()}</em> {xrefs_html}"
                )
            refs_output = True
            has_xrefs = True

        # Entry's references (locators).
        has_refs = False
        entry_refs_html = entry.render_references()
        if entry_refs_html is not None:
            refs_html += (
                TextIndex._category_separator
                if refs_output
                else TextIndex._field_separator
            )
            refs_html += entry_refs_html
            refs_output = True
            has_refs = True

        run_in_children = entry.run_in_children()
        if run_in_children:
            delim = self._category_separator  # if it has_xrefs but not has_refs
            if has_refs:
                delim = self._list_separator
            elif not has_xrefs:
                delim = self._path_separator

            if entry.has_children():
                refs_html += delim
            elif entry.has_also_refs():
                refs_html += self._category_separator

            if entry.has_children():
                child_entries = []
                for child in self.sort_entries(entry.entries):
                    child_entries.append(self.entry_html(child))
                refs_html += self._list_separator.join(child_entries)

        # Check whether we lack children and thus potentially need to inline our
        # own see-also references.
        # This provides run-in style for such references.
        if (
            not entry.has_children() or run_in_children
        ) and entry.has_also_refs():
            also_refs_html = entry.render_also_references()
            if also_refs_html is not None:
                if running_in:
                    refs_html += f" (<em>{self.see_also_label.lower()}</em>"
                else:
                    refs_html += (
                        f"{TextIndex._category_separator}"
                        f"<em>{self.see_also_label.capitalize()}</em>"
                    )
                refs_html = f" {also_refs_html}"
                refs_output = True

        # Create our assembled entry's HTML.
        depth = entry.depth() + 1
        indent = max((2 * depth - 1), 1) * "\t"
        html = f'<span id="{TextIndexEntry._entry_id_prefix}{entry.entry_id}" class="entry-heading">{emphasis(entry.label) if entry.label else ""}</span><span class="entry-references">{refs_html}</span>'
        if not running_in:
            html = f"{indent}<dt>{html}</dt>\n"

        # Handle subordinate indented elements.
        if not run_in_children:
            # Children, if indented.
            if len(entry.entries) > 0:
                html += f"{indent}<dd>\n{indent}\t<dl>\n"
                for child in self.sort_entries(entry.entries):
                    html += self.entry_html(child)
                html += f"{indent}\t</dl>\n{indent}</dd>\n"

        # Parent's see-also cross-references.
        if entry.parent and entry.parent.has_also_refs() and not running_in:
            also_refs_html = entry.parent.render_also_references()
            if also_refs_html is not None:
                html += f'{indent}<dt><span class="entry-references">'
                html += f"<em>{self.see_also_label.capitalize()}</em> {also_refs_html}"
                html += "</span></dt>\n"
                refs_output = True

        return html

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

    def group_heading(self, letter, is_first=False):
        output = ""
        group_headings = self.group_headings_enabled
        if group_headings or not is_first:
            output += f'\t<dt class="group-separator{" group-heading" if group_headings else ""}">{letter if group_headings else "&nbsp;"}</dt>\n'
        return output

    @property
    def group_headings_enabled(self):
        if isinstance(self._group_headings, bool):
            return self._group_headings
        return self._group_headings.lower() == "true"

    @group_headings_enabled.setter
    def group_headings_enabled(self, val) -> None:
        if isinstance(val, str):
            val = val.lower() == "true"
        elif not isinstance(val, bool):
            val = False
        self._group_headings = val
        self._indexed_document = None

    def indexed_document(self):
        if not self._indexed_document:
            self.create_index()
        return self._indexed_document

    def index_html(self, config_string=None):
        if not self._indexed_document:
            self.create_index()

        # Process any parameters in the index directive.
        if config_string:
            config_attrs = {
                TextIndex._prefix: "_index_id_prefix",
                TextIndex.see: "_see_label",
                TextIndex._also: "_see_also_label",
                TextIndex._headings: "_group_headings",
                TextIndex._run_in: "_should_run_in",
                TextIndex._emphasis_first: "_sort_emph_first",
            }
            for key, attr in config_attrs.items():
                param_match = re.search(
                    rf"(?i){key}=(['\"])(.+?)\1", config_string
                )
                if param_match and param_match.group(2):
                    setattr(self, attr, param_match.group(2))

        # Generate HTML.
        html = ""
        if len(self.entries) > 0:
            if self.depth > 1:
                if self.should_run_in:
                    deepest = self.depth + 1
                    self.inform(
                        f"Deep index (>2 levels). Level {deepest} entries will be run-in to level {deepest - 1}. See docs to disable.",
                        severity="warning",
                    )
                else:
                    self.inform(
                        "Deep index (>2 levels). Consider reducing depth, or enable run-in (see docs).",
                        severity="warning",
                    )

            html += f'<dl class="{TextIndex._shared_class} index">\n'
            sorted_entries = self.sort_entries(self.entries)
            letter = sorted_entries[0].sort_on()[0]
            html += self.group_heading(letter, True)
            for entry in sorted_entries:
                next_letter = entry.sort_on()[0]
                if next_letter != letter:
                    html += self.group_heading(next_letter)
                    letter = next_letter
                html += self.entry_html(entry)
            html += "</dl>"
        else:
            self.inform("No index entries defined.", severity="warning")

        # Check size ratio of index to overall document.
        # Remove HTML tags.
        tag_strip_pattern = r"<.*?>"
        stripped_doc = self._indexed_document
        stripped_doc = re.sub(tag_strip_pattern, "", stripped_doc)
        stripped_index = html
        stripped_index = re.sub(tag_strip_pattern, "", stripped_index)
        # Count words approximately.
        wc_pattern = r"\b\w+\b"
        words = re.findall(wc_pattern, stripped_doc)
        wc_doc = len(words)
        words = re.findall(wc_pattern, stripped_index)
        wc_index = len(words)
        # Assess ratio and warn if appropriate.
        ratio = round((wc_index / wc_doc) * 100, 1)
        low_bound, high_bound = 2, 6
        if ratio < low_bound or ratio > high_bound:
            self.inform(
                f"Index might be too {'short' if ratio < low_bound else 'long'} compared to document: ratio is {ratio}% (ideal: {low_bound}–{high_bound}%).",
                severity="warning",
            )
        else:
            self.inform(
                f"Good index size ratio to document: {ratio}% (ideal: {low_bound}–{high_bound}%)."
            )

        return html

    @property
    def index_id_prefix(self):
        return self._index_id_prefix

    @index_id_prefix.setter
    def index_id_prefix(self, val) -> None:
        self._index_id_prefix = val
        self._indexed_document = None

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

    def inform(
        self, msg, severity: str = "normal", force: bool = False
    ) -> None:
        """This method prints an information message to the console with
        optional severity and force flags.

        Args:
            msg (str): The message to be printed.
            severity (str, optional):
                The severity level of the message. Defaults to "normal".
            force (bool, optional):
                A flag to override the verbosity setting and always echo the
                message. Defaults to False.

        Returns:
            None: This method does not return any value.
        """
        if not (
            force
            or self.verbose
            or severity == "warning"
            or severity == "error"
        ):
            return
        out = "TextIndex"
        match severity:
            case "warning":
                out += f" [Warning]: {msg}"
            case "error":
                out += f" [ERROR]: {msg}"
            case _:
                out += f": {msg}"
        print(out)

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
    def see(self) -> str:
        return self._see

    @see.setter
    def see(self, val) -> None:
        self._see = val

    @property
    def see_also_label(self) -> str:
        """Additional cross-reference labels.

        Returns:
            str: Cross-reference label
        """
        return self._see_also_label

    @see_also_label.setter
    def see_also_label(self, val) -> None:
        self._see_also_label = val
        self._indexed_document = None

    @property
    def see_label(self) -> str:
        """Cross reference labels.

        Returns:
            str: Cross-reference label
        """
        return self._see_label

    @see_label.setter
    def see_label(self, val) -> None:
        self._see_label = val
        self._indexed_document = None

    @property
    def should_run_in(self):
        if isinstance(self._should_run_in, bool):
            return self._should_run_in
        return self._should_run_in.lower() == "true"

    @should_run_in.setter
    def should_run_in(self, val) -> None:
        if isinstance(val, str):
            val = val.lower() == "true"
        elif not isinstance(val, bool):
            val = True
        self._should_run_in = val
        self._indexed_document = None

    @property
    def sort_emphasis_first(self) -> bool:
        if isinstance(self._sort_emphasis_first, bool):
            return self._sort_emphasis_first
        return self._sort_emphasis_first.lower() == "true"

    @sort_emphasis_first.setter
    def sort_emphasis_first(self, val) -> None:
        if isinstance(val, str):
            val = val.lower() == "true"
        elif not isinstance(val, bool):
            val = True
        self._sort_emphasis_first = val
        self._indexed_document = None

    def sort_entries(self, entries):
        from operator import methodcaller

        return sorted(entries, key=methodcaller("sort_on"))

    def __bool__(self):
        return True if self._indexed_document else False

    def __len__(self):
        num_entries = 0
        for entry in self.entries:
            num_entries += len(entry)
        return num_entries

    def __str__(self):
        return f"Index ({len(self)} entries)"
