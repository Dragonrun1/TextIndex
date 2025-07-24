# TextIndex, by Matt Gemmell ~ https://mattgemmell.scot/textindex
# Inserts an index into an appropriately-formatted text document.

# Usage:
#		from textindex import textindex
#		index = textindex.TextIndex(book_contents_string)
#		index.verbose = True # To see a LOT of output!
#		book_contents_string = index.indexed_document()

# Or if you just want the (HTML formatted) index itself:
#		from textindex import textindex
#		index = textindex.TextIndex(book_contents_string)
#		index_html = index.index_html()


import re


def emph(text, remove=False):
	# Process Markdown _emphasis_
	replace_val = r"<em>\1</em>" if not remove else r"\1"
	text = re.sub(r"_([^_]+?)_", replace_val, text)
	return text


def elide_end(start, end):
	# Elide the end of a range as much as possible, with an exception for teens.
	# This is a pragmatic approximation of the Chicago Manual of Style convention.
	start_str = str(start)
	end_str = str(end)
	result = end_str
	if len(start_str) == len(end_str) and len(start_str) > 1 and start != end:
		# Trim leftmost matching digits of start/end.
		cut = 0
		while start_str[cut] == end_str[cut]:
			cut += 1
		# Special case: if the numbers are teens (i.e. second-last digit is 1), retain the 1.
		if len(end_str) > 1 and cut == len(end_str) - 1 and end_str[-2] == "1":
			cut -= 1
		result = end_str[cut:]
	
	return int(result)


class TextIndex:

	# Internal use below. For public properties, see end of class definition.
	_see_label = "see"
	_see_also_label = "see also"
	_index_id_prefix = "idx"
	
	# Keys: index placeholder (also vals for cross-references ref-type)
	_see = "see"
	_also = "also"
	_prefix = "prefix"
	
	# Keys: cross-references
	_path = "path"
	_ref_type = "ref-type"
	_reference = "reference" # value for _ref_type key in (non-cross) references
	
	# Directives
	_path_delimiter = ">"
	_refs_delimiter = ";"
	_emphasis_marker = "!"
	_end_marker = "/"
	_also_marker = "+"
	
	# Output
	_range_separator = "–" # en-dash
	_category_separator = ". "
	_field_separator = ", "
	_path_separator = ": "
	_list_separator = "; "
	_shared_class = "textindex"
	
	_index_directive_pattern = r"(?:(?<!\\)\[([^\]<>]+)(?<!\\)\]|([^\s\[\]\{\}<>]++))*(?<!>)\{\^([^\}<\n]*)\}(?!<)"
	_index_placeholder_pattern = r"(?im)^\{index\s*([^\}]*)\s*\}"
	_disable = "-"
	_enable = "+"
	
	
	def __init__(self, document_text=None):
		self.original_document = document_text
		self.entries = []
		self._see_label = TextIndex._see_label
		self._see_also_label = TextIndex._see_also_label
		self._index_id_prefix = TextIndex._index_id_prefix
		self._indexed_document = None
		self.verbose = False
	
	
	def inform(self, msg, severity="normal", force=False):
		should_echo = (force or self.verbose or severity=="warning" or severity=="error")
		if should_echo:
			out = ""
			prefix = "TextIndex"
			match severity:
				case "warning":
					out = f" [Warning]: {msg}"
				case "error":
					out = f" [ERROR]: {msg}"
					should_echo = True
				case _:
					out = f": {msg}"
			print(f"{prefix}{out}")
	
	
	def create_index(self):
		entry_number = 0
		if self.original_document:
			indexed_doc = self.original_document
			alias_prefix = "#"
			#alias_token_pattern = rf"(?<!{alias_prefix}){alias_prefix}([a-zA-Z0-9\-_]+)"
			alias_definition_pattern = rf"{alias_prefix}({alias_prefix}?[a-zA-Z0-9\-_]+)$"
			aliases = {}
			alias_path = "path"
			
			# Find all directives.
			offset = 0 # accounting for replacements
			enabled = True
			directive_matches = re.finditer(TextIndex._index_directive_pattern, self.original_document)
			for directive in directive_matches:
				
				# Parse and encapsulate each entry, either as an object or a range-end.
				self.inform(f"Directive found: {directive.group(0)}")
				
				params = directive.group(3).strip()
				closing = False
				emphasis = False
				sort_key = None
				suffix = None
				cross_references = []
				
				# Determine type of directive.
				toggling_directive = (params == TextIndex._enable or params == TextIndex._disable)
				status_toggled = False
				if params.endswith(self._end_marker):
					closing = True
					params = params[:-len(self._end_marker)]
					self.inform(f"\tClosing mark: /")
				elif params.endswith(self._emphasis_marker):
					emphasis = True
					params = params[:-len(self._emphasis_marker)]
					self.inform(f"\tLocator Emphasis: !")
				elif params == TextIndex._enable and not enabled:
					enabled = True
					self.inform(f"============ Processing enabled.  ============")
					status_toggled = True
				elif params == TextIndex._disable and enabled:
					enabled = False
					self.inform(f"============ Processing disabled. ============")
					status_toggled = True
				
				if toggling_directive and (enabled or status_toggled):
					# This was a toggling mark, and we're either now enabled or we were when we encountered it.
					# Remove the mark.
					indexed_doc = indexed_doc[:directive.start() + offset] + indexed_doc[directive.end() + offset:]
					delta = 0 - len(directive.group(0))
					offset += delta
				
				if not enabled or status_toggled or toggling_directive:
					continue
				
				# Determine label path.
				label = None
				label_path_components = []
				if directive.group(1): # leading bracketed span
					label = directive.group(1)
				elif directive.group(2): # leading implicit non-whitespace span
					label = directive.group(2)
				span_contents = label # for replacement
				
				# Still need to check for a label path within the directive.
				label_match = re.match(r"^([^\|\[~]+)", params)
				if label_match:
					label_match_text = label_match.group(0).strip()
					
					# Process aliases before splitting path.
					if len(aliases) > 0 and len(label_match_text) > 0:
						# Ensure we replace longer alias-names first, to avoid spurious prefix matches.
						longest_first = dict(sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True))
						for key, val in longest_first.items():
							expanded = self._path_delimiter.join(f'"{elem}"' for elem in val[alias_path])
							label_match_text = re.sub(rf"(?<!{alias_prefix}){alias_prefix}{key}", expanded, label_match_text)
					
					# Handle search wildcards.
					if label:
						search_wildcard_pattern = r"\*\^(\-?)"
						replacement = "*" # fall back on basic wildcard functionality.
						found_item = None
						replace_label = None
						replace_path = None
						found_wildcards = list(re.finditer(search_wildcard_pattern, label_match_text))
						if len(found_wildcards) > 0:
							found_item = self.prefix_search(label)
						if found_item:
							replace_label = f'"{found_item.label}"'
							replace_path = self._path_delimiter.join(f'"{elem}"' for elem in found_item.path_list())
						for found_wildcard in reversed(found_wildcards):
							if found_item:
								label_only = (found_wildcard.group(1) != "")
								if label_only:
									replacement = replace_label
								else:
									replacement = replace_path
								self.inform(f"\tFound {'(label-only) ' if label_only else ''}prefix match for '{label}': {replacement}")
							label_match_text = label_match_text[:found_wildcard.start()] + replacement + label_match_text[found_wildcard.end():]
					
					# Split label path.
					label_path_components = label_match_text.split(self._path_delimiter)
					
					# Having already replaced alias references, check for alias definition at end of label path.
					alias_definition_match = re.search(alias_definition_pattern, label_path_components[-1])
					if alias_definition_match:
						label_path_components[-1] = label_path_components[-1][:alias_definition_match.start()]
					
					# Remove quotes from path elements.
					label_path_components = [component.strip("'\"") for component in label_path_components]
					
					# Process wildcards only if there's a preceding label to use for replacement.
					if label:
						# Handle replacing static wildcards with processed label.
						label_path_components = [component.replace("**", emph(label, True).lower()) for component in label_path_components]
						label_path_components = [component.replace("*", emph(label, True)) for component in label_path_components]
					
					last_component = label_path_components[-1]
					if last_component != self._path_delimiter and last_component != "":
						label = last_component
						label_path_components.pop() # remove last item, which is now the label.
					if len(label_path_components) > 0 and label_path_components[-1] == "":
						label_path_components.pop() # remove empty last item.
					
					# Trim label path from params.
					params = params[:label_match.start()] + params[label_match.end():]
					
					# Check for alias definition.
					alias_without_reference = False
					if alias_definition_match:
						alias_name = alias_definition_match.group(1)
						if alias_name.startswith(alias_prefix):
							alias_without_reference = True
							alias_name = alias_name.lstrip(alias_prefix)
						
						if alias_definition_match.start() > 0:
							# Alias definition at end of an internally-specified label.
							# Trim alias portion from label, and define.
							aliases[alias_name] = {alias_path: label_path_components + [label]}
							self.inform(f"\tDefined alias {alias_prefix}{alias_name} as: {aliases[alias_name]}")
						else:
							# Alias found at start of label. Either an alias reference, or a definition without an internal label (foo>#bar or just #bar).
							if len(label_path_components) == 0:
								# No path components. Could be an alias definition at root, or an alias reference. Try to load the alias.
								if alias_name in aliases:
									# It's a valid alias reference. Load alias.
									label = aliases[alias_name][alias_label]
									label_path_components = aliases[alias_name][alias_path]
									self.inform(f"\tLoaded alias {aliases[alias_name]} for directive: {directive.group(0)}")
								else:
									# No path components, and an alias reference to a non-existent alias. Define a new alias instead.
									if span_contents and len(span_contents) > 0:
										label = span_contents
										aliases[alias_name] = {alias_path: label_path_components + [label]}
										self.inform(f"\tDefined alias {alias_prefix}{alias_name} as: {aliases[alias_name]}")
							else:
								# Path components exist, so this is an alias definition without an internal label.
								if span_contents and len(span_contents) > 0:
									# We already had a label from either a bracketed span, or implicitly. Define alias.
									label = span_contents
									aliases[alias_name] = {alias_path: label_path_components + [label]}
									self.inform(f"\tDefined alias {alias_prefix}{alias_name} as: {aliases[alias_name]}")
								else:
									# No label specified either internally or previously; can't define an alias.
									label = None
									self.inform(f"Alias definition without a label: {directive.group(0)}", severity="warning")
						
						if alias_without_reference:
							if label:
								self.inform(f"\tUnreferenced alias created; skipping rest of directive: {directive.group(0)}")
							else:
								self.inform(f"\tUnreferenced alias definition without a label; skipping rest of directive: {directive.group(0)}", severity="warning")
							
							# Replace directive in indexed_document.
							span_html = f'{emph(span_contents) if span_contents else ''}'
							indexed_doc = indexed_doc[:directive.start() + offset] + span_html + indexed_doc[directive.end() + offset:]
							delta = len(span_html) - len(directive.group(0))
							offset += delta
							continue
					
				self.inform(f"\tLabel: {label}")
				if len(label_path_components) > 0:
					self.inform(f"\tPath: {label_path_components}")
				
				if not label:
					self.inform(f"No entry label specified in directive. Ignoring: {directive.group(0)}", severity="warning")
					continue
				
				# Suffix.
				params = params.strip()
				suffix_match = re.search(r"\s*\[([^\]]+)(?<!\\)\]\s*", params)
				if suffix_match:
					suffix = suffix_match.group(1)
					params = params[:suffix_match.start()] + params[suffix_match.end():]
					self.inform(f"\tSuffix: {suffix}")
				
				# Sort key.
				params = params.strip()
				sort_match = re.search(r"\s*\~(['\"]?)(.+)\1$", params)
				if sort_match:
					sort_key = sort_match.group(2)
					self.inform(f"\tSort as: {sort_key}")
					params = params[:sort_match.start()] + params[sort_match.end():]
				
				# Cross-references.
				cross_match = re.match(r"\|(.+)$", params)
				create_ref = True
				if cross_match:
					refs_string = cross_match.group(1).strip()
					
					# Process aliases before splitting path.
					if len(aliases) > 0 and len(refs_string) > 0:
						# Ensure we replace longer alias-names first, to avoid spurious prefix matches.
						longest_first = dict(sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True))
						for key, val in longest_first.items():
							expanded = self._path_delimiter.join(f'"{elem}"' for elem in val[alias_path])
							refs_string = re.sub(rf"(?<!{alias_prefix}){alias_prefix}{key}", expanded, refs_string)
					
					refs = refs_string.split(self._refs_delimiter)
					for ref in refs:
						ref_type = self._see
						ref = ref.strip()
						if ref.startswith(self._also_marker):
							ref_type = self._also
							ref = ref[len(self._also_marker):]
						else:
							# Don't create a (page-)reference if there's a (non-also) cross-reference.
							create_ref = False
						ref_path_components = ref.split(self._path_delimiter)
						ref_path_components = [component.strip("'\"") for component in ref_path_components]
						
						cross_references.append({self._ref_type: ref_type, self._path: ref_path_components})
					
					params = params[:cross_match.start()] + params[cross_match.end():]
					self.inform(f"\tCross-refs: {cross_references}")
				
				if len(params.strip()) > 0:
					self.inform(f"Unparsed directive content: '{params}' (please report this!)", severity="warning")
				
				# Prepare next reference id.
				entry_number += 1
				
				# Insert into entries tree.
				entry, existed = self.entry_at_path(label, label_path_components, not closing)
				display_entry_path = f' {self._path_delimiter} '.join(label_path_components + [label])
				if not entry and closing:
					# Entry doesn't exist, but we're trying to end its (non-existent) range.
					self.inform(f"Attempted to close non-existent entry \"{display_entry_path}\". Ignoring: {directive.group(0)}", severity="warning")
					continue
				elif entry and closing:
					# Entry exists, and we're closing its range. If it already has a closing ID, update it.
					if len(entry.references) > 0:
						if TextIndexEntry.end_id in entry.references[-1]:
							self.inform(f"Altering existing end-location of range for reference \"{display_entry_path}\": {directive.group(0)}", severity="warning")
						entry.update_latest_ref_end(entry_number, suffix)
						self.inform(f"\tSet end-location for reference to \"{display_entry_path}\".")
					else:
						# Entry exists, but has no references, so we can't set an end id.
						self.inform(f"Attempted to close non-existent reference for existing entry \"{display_entry_path}\". Ignoring: {directive.group(0)}", severity="warning")
				else:
					# We now have the correct entry, whether it existed before or not. Populate.
					if create_ref:
						entry.add_reference(entry_number, suffix, emphasis)
					elif suffix or emphasis:
						self.inform(f"Ignoring suffix/emphasis in cross-reference: {directive.group(0)}", severity="warning")
					
					if sort_key:
						if entry.sort_key:
							self.inform(f"Altering existing sort-key for reference \"{display_entry_path}\" (was '{entry.sort_key}', now '{sort_key}'). Directive was: {directive.group(0)}", severity="warning")
						entry.sort_key = sort_key
					if len(cross_references) > 0:
						entry.cross_references = entry.cross_references + cross_references
						if existed:
							self.inform(f"\tAdded cross-references to existing entry '{label}'")
				
				# Replace directive in indexed_document with suitable span.
				span_html = f'<span id="{self.index_id_prefix}{entry_number}" class="{TextIndex._shared_class}">{emph(span_contents) if span_contents else ''}</span>'
				indexed_doc = indexed_doc[:directive.start() + offset] + span_html + indexed_doc[directive.end() + offset:]
				delta = len(span_html) - len(directive.group(0))
				offset += delta
			
			self.inform(f"{len(self)} entries created.", force=True)
			
			# Replace each index placeholder with a suitable HTML index.
			self._indexed_document = indexed_doc # needs an initial value otherwise index_html() will recurse.
			indexed_doc = re.sub(TextIndex._index_placeholder_pattern, self.index_replace, indexed_doc)
		
		self._indexed_document = indexed_doc
	
	
	def entry_at_path(self, label, path_list, create=True):
		# Returns entry named label at path path_list, and whether it already existed or not.
		# If entry doesn't exist and create is True, creates it; else returns None.
		
		created = False
		entry = None
		entries = self.entries
		
		for component in (path_list + [label]):
			#found_entry = next((ent for ent in entries if ent.label == component), None)
			found_entry = None
			for ent in entries:
				#print(f"\tChecking '{ent.label}' against '{component}'")
				if ent.label == component:
					#print(f"\tFound {component}")
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
				else:
					self.inform(f"\tMaking new entry '{component}' ({'within \'' + entry.label + '\'' if entry else 'at root'})")
					new_entry = TextIndexEntry(component, entry)
					entries.append(new_entry)
					entries = new_entry.entries
					entry = new_entry
					created = True # If we create any entry in the chain, we create all subsequent ones too.
		
		return entry, (entry and not created)
	
	
	def indexed_document(self):
		if not self._indexed_document: self.create_index()
		return self._indexed_document
	
	
	def index_replace(self, the_match):
		return self.index_html(the_match.group(1))
		
	
	def index_html(self, config_string=None):
		if not self._indexed_document: self.create_index()
		
		if config_string:
			config_attrs = {
											TextIndex._prefix: '_index_id_prefix',
											TextIndex._see: '_see_label',
											TextIndex._also: '_see_also_label'
											}
			for key, attr in config_attrs.items():
				param_match = re.search(rf"(?i){key}=(['\"])(.+?)\1", config_string)
				if param_match and param_match.group(2):
					setattr(self, attr, param_match.group(2))
		
		html = ""
		if len(self.entries) > 0:
			html += f'<dl class="{TextIndex._shared_class} index">\n'
			sorted_entries = self.sort_entries(self.entries)
			#letter = emph(sorted_entries[0].label, True)[0].lower()
			letter = sorted_entries[0].sort_on()[0]
			for entry in sorted_entries:
				#next_letter = emph(entry.label, True)[0].lower()
				next_letter = entry.sort_on()[0]
				if next_letter != letter:
					html += '\t<dt class="group-separator">&nbsp;</dt>\n'
					letter = next_letter
				html += self.entry_html(entry)
			html += "</dl>"
		else:
			self.inform(f"No index entries defined.", severity="warning")
		return html
	
	
	def entry_html(self, entry):
		refs_html = ""
		
		# Cross-refs (non-also), then ordered references, then parent's also-refs.
		refs_output = False
		if len(entry.cross_references) > 0:
			for i in range(len(entry.cross_references)):
				ref = entry.cross_references[i]
				if ref[TextIndex._ref_type] == TextIndex._see:
					refs_output = True
					refs_html += (TextIndex._refs_delimiter if i > 0 else f'{TextIndex._category_separator}<em>{self.see_label.capitalize()}</em>')
					refs_html += f' {TextIndex._path_separator.join(ref[TextIndex._path])}'
		
		if len(entry.references) > 0:
			loc_class = "locator"
			for i in range(len(entry.references)):
				ref = entry.references[i]
				refs_html += (TextIndex._category_separator if refs_output and i == 0 else TextIndex._field_separator)
				locator_html = ""
				
				locator_html += f'<a class="{loc_class}" href="#{self.index_id_prefix}{ref[TextIndexEntry.start_id]}" data-index-id="{ref[TextIndexEntry.start_id]}" data-index-id-elided="{ref[TextIndexEntry.start_id]}"></a>'
				if TextIndexEntry.end_id in ref:
					elided_end = elide_end(ref[TextIndexEntry.start_id], ref[TextIndexEntry.end_id])
					locator_html += TextIndex._range_separator
					locator_html += f'<a class="{loc_class}" href="#{self.index_id_prefix}{ref[TextIndexEntry.end_id]}" data-index-id="{ref[TextIndexEntry.end_id]}" data-index-id-elided="{elided_end}"></a>'
				if TextIndexEntry.suffix in ref and ref[TextIndexEntry.suffix]:
					locator_html += f' {ref[TextIndexEntry.suffix]}'
				if TextIndexEntry.end_suffix in ref and ref[TextIndexEntry.end_suffix]:
					locator_html += f' {ref[TextIndexEntry.end_suffix]}'
				if ref[TextIndexEntry.locator_emphasis]:
					locator_html = f"<em>{locator_html}</em>"
				refs_output = True
				
				refs_html += locator_html
		
		# Check whether we lack children and thus potentially need to inline our own see-also references.
		# This provides run-in style for such references.
		if len(entry.entries) == 0 and self.has_also_refs(entry):
			refs_output = False
			for i in range(len(entry.cross_references)):
				ref = entry.cross_references[i]
				if ref[TextIndex._ref_type] == TextIndex._also:
					refs_html += (TextIndex._refs_delimiter if refs_output else f'{TextIndex._category_separator}<em>{self.see_also_label.capitalize()}</em>')
					refs_html += f' {TextIndex._path_separator.join(ref[TextIndex._path])}'
					refs_output = True
		
		depth = entry.depth() + 1
		indent = max((2 * depth - 1), 1) * '\t'
		html = f'{indent}<dt><span class="entry-heading">{emph(entry.label) if entry.label else ""}</span><span class="entry-references">{refs_html}</span></dt>\n'
		
		# Children
		if len(entry.entries) > 0:
			html += f'{indent}<dd>\n{indent}\t<dl>\n'
			for child in self.sort_entries(entry.entries):
				html += self.entry_html(child)
			html += f'{indent}\t</dl>\n{indent}</dd>\n'
		'''
		else:
			# No children, so check for our own see-also cross-references, and use a dummy child if appropriate.
			# This provides flush-and-hang/indented style for such references.
			if self.has_also_refs(entry):
				html += f'{indent}<dd>\n{indent}\t<dl>\n'
				html += self.entry_html(TextIndexEntry(None, entry))
				html += f'{indent}\t</dl>\n{indent}</dd>\n'
		'''
		# Parent's see-also cross-references.
		if self.has_also_refs(entry.parent):
			refs_output = False
			for i in range(len(entry.parent.cross_references)):
				ref = entry.parent.cross_references[i]
				if ref[TextIndex._ref_type] == TextIndex._also:
					if not refs_output:
						html += f'{indent}<dt><span class="entry-references">'
					html += (TextIndex._refs_delimiter if refs_output else f'<em>{self.see_also_label.capitalize()}</em>')
					html += f' {TextIndex._path_separator.join(ref[TextIndex._path])}'
					refs_output = True
			if refs_output:
				html += '</span></dt>\n'		
		
		
		return html
	
	
	def has_also_refs(self, entry):
		also_xrefs = False
		if entry and len(entry.cross_references) > 0:
			for ent in entry.cross_references:
				if ent[TextIndex._ref_type] == TextIndex._also:
					also_xrefs = True
					break
		return also_xrefs
	
	
	def sort_entries(self, entries):
		from operator import methodcaller
		return sorted(entries, key=methodcaller('sort_on'))
	
	
	def get_see_label(self):
		return self._see_label
	
	
	def get_see_also_label(self):
		return self._see_also_label
	
	
	def get_index_id_prefix(self):
		return self._index_id_prefix
	
	
	def set_see_label(self, val):
		self._see_label = val
		self._indexed_document = None
	
	
	def set_see_also_label(self, val):
		self._see_also_label = val
		self._indexed_document = None
	
	
	def set_index_id_prefix(self, val):
		self._index_id_prefix = val
		self._indexed_document = None
	
	def prefix_search(self, text):
		found = None
		for entry in self.entries:
			found = entry.prefix_search(text)
			if found:
				break
		return found
	
	def __len__(self):
		num_entries = 0
		for entry in self.entries:
			num_entries += len(entry)
		return num_entries
	
	
	def __bool__(self):
		return True if self._indexed_document else False
	
	
	def __str__(self):
		return f"Index ({len(self)} entries)"
	
	
	# Configurable in {index} blocks, or directly.
	see_label = property(get_see_label, set_see_label)
	see_also_label = property(get_see_also_label, set_see_also_label)
	index_id_prefix = property(get_index_id_prefix, set_index_id_prefix)


class TextIndexEntry:

	# Keys for dicts in instances' self.references list.
	start_id = "start-id"
	end_id = "end-id"
	suffix = "suffix"
	end_suffix = "end-suffix"
	locator_emphasis = "locator-emphasis"
	
	
	def __init__(self, label=None, parent=None):
		self.label = label
		self.parent = parent
		self.entries = [] # children
		self.references = [] # list of dicts; see keys above.
		self.cross_references = []
		self.sort_key = None
	
	
	def sort_on(self):
		return (self.sort_key if self.sort_key else emph(self.label, True)).lower()
	
	
	def add_reference(self, start_id, suffix=None, locator_emphasis=False):
		self.references.append({
														TextIndex._ref_type: TextIndex._reference,
														self.start_id: start_id,
														self.suffix: suffix,
														self.locator_emphasis: locator_emphasis
													})
		
	
	def update_latest_ref_end(self, end_id, end_suffix=None):
		self.references[-1][self.end_id] = end_id
		if end_suffix:
			self.references[-1][self.end_suffix] = end_suffix
	
	
	def depth(self):
		level = 0
		par = self.parent
		while par:
			par = par.parent
			level += 1
		return level
	
	def prefix_search(self, text):
		found = None
		if self.label.startswith(text):
			return self
		for entry in self.entries:
			found = entry.prefix_search(text)
			if found:
				break
		return found
	
	def path_list(self):
		components = [self.label]
		par = self.parent
		while par:
			components.insert(0, par.label)
			par = par.parent
		return components
	
	def __str__(self):
		return f"Entry: {self.label} [{len(self.entries)} children]"
	
	
	def __bool__(self):
		return True
	
	
	def __repr__(self):
		return self.__str__()
	
	
	def __len__(self):
		num_entries = 1
		for entry in self.entries:
			num_entries += len(entry)
		return num_entries
