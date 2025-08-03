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
	_group_headings = False
	_should_run_in = True
	_sort_emph_first = False
	
	# Keys: index placeholder (also vals for cross-references ref-type)
	_see = "see"
	_also = "also"
	_prefix = "prefix"
	_headings = "headings"
	_run_in = "run-in"
	_emph_first = "emph-first"
	
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
	_inbound_marker = "@"
	
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
	
	
	_alias_prefix = "#"
	_alias_token_pattern = rf"(?<!{_alias_prefix}){_alias_prefix}([a-zA-Z0-9\-_]+)"
	_alias_definition_pattern = rf"{_alias_prefix}({_alias_prefix}?[a-zA-Z0-9\-_]+)$"
	_alias_path = "path"
	
	
	def __init__(self, document_text=None):
		self.original_document = document_text
		self.intermediate_document = None
		self.entries = []
		self._see_label = TextIndex._see_label
		self._see_also_label = TextIndex._see_also_label
		self._index_id_prefix = TextIndex._index_id_prefix
		self._group_headings = TextIndex._group_headings
		self._should_run_in = TextIndex._should_run_in
		self._sort_emph_first = TextIndex._sort_emph_first
		self._indexed_document = None
		self.verbose = False
		self.aliases = {}
		self.depth = 0 # zero-based greatest depth
	
	
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
	
	
	def load_concordance_file(self, path):
		if not self.original_document or self.original_document == "":
			self.inform(f"No document to index; ignoring concordance file.", severity="warning")
			return
		
		# Load file.
		import os
		conc_contents = None
		concordance = []
		try:
			path = os.path.abspath(os.path.expanduser(path))
			conc_file = open(path, 'r')
			conc_contents = conc_file.read()
			conc_file.close()
		
		except IOError as e:
			self.inform(f"Couldn't open concordance file: {e}", severity="error")
			return
		
		if not conc_contents:
			self.inform(f"Couldn't read concordance file: {path}", severity="error")
		
		# Duplicate original document to work with.
		conc_doc = f"{self.intermediate_document if self.intermediate_document else self.original_document}"
		
		# Parse into entry-pattern lines.
		for line in conc_contents.split("\n"):
			if line.startswith("#") or re.fullmatch(r"^\s*$", line):
				continue
			line = re.sub(r"\t+", "\t", line) # Collapse tab-runs
			components = line.strip('\n').split("\t") # split into columns
			if len(components) > 0:
				case_sensitive = False
				if components[0].startswith("\\="):
					# Since we use = as a prefix for case-sensitive, allow \= for literal equals by stripping \.
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
					components.append("") # Ensure second column for simplicity.
				
				concordance.append(components[:2]) # Discard anything after 2nd column.
		
		# Parse document for TextIndex marks, index directive, and HTML tag ranges to exclude.
		excluded_ranges = []
		excl_pattern = f"{self._index_placeholder_pattern}|(?:{self._index_directive_pattern})|<.*?>"
		excl_matches = re.finditer(excl_pattern, conc_doc)
		for excl in excl_matches:
			excluded_ranges.append([excl.start(), excl.end()])
			#print(f"Excluded range of: {excl.group(0)} ({excl.start()}, {excl.end()})")
		
		# Process concordance entries.
		term_ranges = []
		for conc in concordance:
			# Match and replace this term expression wherever it doesn't intersect excluded ranges.
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
					elif start >= term.end():
						# This excluded range starts after term. We're done.
						break
					elif term.start() >= start or term.end() <= end:
						# This excluded range intersects term. Abort replacement.
						is_excluded = True
						#print(f"*** Excluded range '{self.original_document[start:end]}' intersects '{term.group(0)}' ***")
						break
				
				if not is_excluded:
					term_ranges.append([term.start(), term.end(), term.group(0), conc[1]])
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
				conc_doc = conc_doc[:term[0] + offset] + mark + conc_doc[term[1] + offset:]
				offset += (len(mark) - len(term[2]))
				marks_added += 1
		
		# Make the intermediate concorded document available.
		self.intermediate_document = conc_doc
		
		# Log results.
		self.inform(f"Concordance file processed. {len(concordance)} rules generated {marks_added} index marks.", force=True)

	
	def convert_latex_index_commands(self):
		if not self.original_document:
			self.inform(f"No original document text; can't convert latex commands.", severity="warning")
			return
		
		text = f"{self.intermediate_document if self.intermediate_document else self.original_document}"
		offset = 0
		marks_converted = 0
		
		latex_index_cmd_start = r"\\index\{"
		latex_matches = re.finditer(latex_index_cmd_start, text)
		for lmark in latex_matches:
			# Scan string to find end of \index{…} command, ensuring all braces are balanced.
			quit_after = 150
			braces_open = 1
			idx = lmark.end() + offset
			while braces_open > 0 and idx < (len(text) - 1) and (idx - lmark.end() + offset) < quit_after:
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
			cmd_content = entire_cmd[len(lmark.group(0)):-1]
			
			# Check for continuing locator syntax.
			continuing = False
			cont_match = re.search(r"\|([\(\)])$", cmd_content)
			if cont_match:
				if cont_match.group(1) == ")":
					continuing = True
				cmd_content = cmd_content[:0 - len(cont_match.group(0))]
			
			# Deal with emphasis commands, brace-wrapped.
			cmd_content = re.sub(r"(?i)\\(?:textbf|textit|textsl|emph)\{([^\}]+)\}", r"_\1_", cmd_content)
			
			# Check for sort key (up to @).
			sort_key = None
			sort_match = re.match(r"([^@]+)@", cmd_content)
			if sort_match:
				sort_key = sort_match.group(1)
				cmd_content = cmd_content[sort_match.end():]
			
			# Check for locator emphasis (braceless commands after |).
			loc_emph = False
			loc_emph_match = re.search(r"\|(?:textbf|textit|textsl|emph)$", cmd_content)
			if loc_emph_match:
				loc_emph = True
				cmd_content = cmd_content[:loc_emph_match.start()]
			
			# Check for cross-references of both types.
			xref = None
			xref_match = re.search(r"\|(see(?:also)?)\s*\{([^\}]+)\}$", cmd_content)
			if xref_match:
				ref_type = xref_match.group(1)
				ref_path = xref_match.group(2)
				path_bits = re.split(r",\s*", ref_path)
				ref_path = ">".join(f'"{elem}"' for elem in path_bits)
				xref = f"{'+' if ref_type == 'seealso' else ''}{ref_path}"
				cmd_content = cmd_content[:xref_match.start()]
			
			# Deal with hierarchy and quoting in heading.
			heading_parts = cmd_content.split("!")
			heading_path = ">".join(f'"{elem}"' for elem in heading_parts)
			
			# Construct suitable index mark.
			mark_parts = [heading_path]
			if xref:
				mark_parts.append(f"|{xref}")
			if sort_key:
				mark_parts.append(f"~\"{sort_key}\"")
			if continuing:
				mark_parts.append("/")
			elif loc_emph:
				mark_parts.append("!")
			mark = f"{{^{' '.join(mark_parts)}}}"
			self.inform(f"Converted latex index command:  {entire_cmd}  -->  {mark}")
			
			# Replace in document, maintaining text-delta offset.
			text = text[:start] + mark + text[end:]
			offset += (len(mark) - len(entire_cmd))
			marks_converted += 1
		
		plural = '' if marks_converted == 1 else 's'
		self.inform(f"{marks_converted} latex index command{plural} converted to index mark{plural}.", force=True)
		
		self.intermediate_document = text
	
	
	def create_index(self):
		entry_number = 0
		if self.original_document:
			indexed_doc = f"{self.intermediate_document if self.intermediate_document else self.original_document}"
			self.aliases = {}
			
			# Find all directives.
			offset = 0 # accounting for replacements
			enabled = True
			directive_matches = re.finditer(TextIndex._index_directive_pattern, indexed_doc)
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
					if len(self.aliases) > 0 and len(label_match_text) > 0:
						label_match_text = re.sub(TextIndex._alias_token_pattern, self.alias_replace, label_match_text)
					
					# Handle wildcards in label path.
					label_match_text = self.process_wildcards(label, label_match_text)
					
					# Split label path.
					label_path_components = label_match_text.split(self._path_delimiter)
					
					# Having already replaced alias references, check for alias definition at end of label path.
					alias_definition_match = re.search(TextIndex._alias_definition_pattern, label_path_components[-1])
					if alias_definition_match:
						label_path_components[-1] = label_path_components[-1][:alias_definition_match.start()]
					
					# Remove quotes from path elements.
					label_path_components = [component.strip("'\"") for component in label_path_components]
					
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
						if alias_name.startswith(TextIndex._alias_prefix):
							alias_without_reference = True
							alias_name = alias_name.lstrip(TextIndex._alias_prefix)
						
						if alias_definition_match.start() > 0:
							# Alias definition at end of an internally-specified label.
							# Trim alias portion from label, and define.
							self.define_alias(alias_name, label_path_components + [label])
						else:
							# Alias found at start of label. Either an alias reference, or a definition without an internal label (foo>#bar or just #bar).
							if len(label_path_components) == 0:
								# No path components. Could be an alias definition at root, or an alias reference. Try to load the alias.
								if alias_name in self.aliases:
									# It's a valid alias reference. Load alias.
									label = self.aliases[alias_name][alias_label]
									label_path_components = self.aliases[alias_name][TextIndex._alias_path]
									self.inform(f"\tLoaded alias {self.aliases[alias_name]} for directive: {directive.group(0)}")
								else:
									# No path components, and an alias reference to a non-existent alias. Define a new alias instead.
									if span_contents and len(span_contents) > 0:
										label = span_contents
										self.define_alias(alias_name, label_path_components + [label])
							else:
								# Path components exist, so this is an alias definition without an internal label.
								if span_contents and len(span_contents) > 0:
									# We already had a label from either a bracketed span, or implicitly. Define alias.
									label = span_contents
									self.define_alias(alias_name, label_path_components + [label])
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
					
					# Handle wildcards in sort key.
					sort_key = self.process_wildcards(span_contents, sort_key, True)
					
					self.inform(f"\tSort as: {sort_key}")
					params = params[:sort_match.start()] + params[sort_match.end():]
				
				# Cross-references.
				cross_match = re.match(r"\|(.+)$", params)
				create_ref = True
				if cross_match:
					refs_string = cross_match.group(1).strip()
					
					# Process aliases before splitting path.
					if len(self.aliases) > 0 and len(refs_string) > 0:
						refs_string = re.sub(TextIndex._alias_token_pattern, self.alias_replace, refs_string)
					
					# Handle wildcards in cross-refs.
					refs_string = self.process_wildcards(span_contents, refs_string)
					
					refs = refs_string.split(self._refs_delimiter)
					for ref in refs:
						inbound = False
						ref_type = self._see
						ref = ref.strip()
						
						if ref.startswith(self._inbound_marker):
							inbound = True
							ref = ref[len(self._inbound_marker):]
						
						if ref.startswith(self._also_marker):
							ref_type = self._also
							ref = ref[len(self._also_marker):]
						elif not inbound:
							# Don't create a (page-)reference for this mark's entry if there's a (non-also) cross-reference.
							create_ref = False
						
						ref_path_components = ref.split(self._path_delimiter)
						ref_path_components = [component.strip("'\"") for component in ref_path_components]
						
						if inbound:
							# Cross-ref in different entry, referencing this mark's entry. Find other entry.
							source_label = ref_path_components[-1]
							source_path_components = []
							if len(ref_path_components) > 1:
								source_path_components = ref_path_components[:-1]
							source_entry, existed = self.entry_at_path(source_label, source_path_components, True)
							self.inform(f"\tCreating inbound '{ref_type}' cross-reference from entry '{source_label}' {'(Path: ' + source_path_components + ')' if len(ref_path_components) > 1 else '(at root)'}")
							source_entry.add_cross_reference(ref_type, label_path_components + [label])
							
						else:
							# Cross-ref within this mark's entry.
							cross_references.append({self._ref_type: ref_type, self._path: ref_path_components})
					
					params = params[:cross_match.start()] + params[cross_match.end():]
					if len(cross_references) > 0:
						self.inform(f"\tCross-refs: {cross_references}")
				
				if len(params.strip()) > 0:
					self.inform(f"*** Unparsed directive content: '{params}' (please report this!) ***", severity="warning")
				
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
						if entry.sort_key and entry.sort_key != sort_key:
							self.inform(f"Altering existing sort-key for reference \"{display_entry_path}\" (was '{entry.sort_key}', now '{sort_key}'). Directive was: {directive.group(0)}", severity="warning")
						entry.sort_key = sort_key
					if len(cross_references) > 0:
						for ref in cross_references:
							entry.add_cross_reference(ref[self._ref_type], ref[self._path])
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
	
	
	def define_alias(self, name, path):
		redefinition = False
		if name in self.aliases and self.aliases[name][TextIndex._alias_path] != path:
				# Redefinition of existing alias.
				redefinition = True
		
		self.aliases[name] = {TextIndex._alias_path: path}
		self.inform(f"\t{'Redefined existing' if redefinition else 'Defined new'} alias {TextIndex._alias_prefix}{name} as: {self.aliases[name]}")
	
	def entry_at_path(self, label, path_list, create=True):
		# Returns entry named label at path path_list, and whether it already existed or not.
		# If entry doesn't exist and create is True, creates it; else returns None.
		
		created = False
		entry = None
		entries = self.entries
		
		for component in (path_list + [label]):
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
				else:
					self.inform(f"\tMaking new entry '{component}' ({'within \'' + entry.label + '\'' if entry else 'at root'})")
					new_entry = TextIndexEntry(component, entry)
					new_entry.textindex = self
					entry_depth = new_entry.depth()
					if entry_depth > self.depth:
						self.depth = entry_depth
					entries.append(new_entry)
					entries = new_entry.entries
					entry = new_entry
					created = True # If we create any entry in the chain, we create all subsequent ones too.
		
		return entry, (entry and not created)
	
	
	def process_wildcards(self, label, text, force_label_only=False):
		if label:
			search_wildcard_pattern = r"\*\^(\-?)"
			replacement = "*" # fall back on basic wildcard functionality.
			found_item = None
			replace_label = None
			replace_path = None
			found_wildcards = list(re.finditer(search_wildcard_pattern, text))
			if len(found_wildcards) > 0:
				found_item = self.prefix_search(label)
			if found_item:
				replace_label = f'"{found_item.label}"'
				replace_path = self._path_delimiter.join(f'"{elem}"' for elem in found_item.path_list())
			for found_wildcard in reversed(found_wildcards):
				if found_item:
					label_only = (found_wildcard.group(1) != "") or force_label_only
					if label_only:
						replacement = replace_label
					else:
						replacement = replace_path
					self.inform(f"\tFound {'(label-only) ' if label_only else ''}prefix match for '{label}': {replacement}")
				text = text[:found_wildcard.start()] + replacement + text[found_wildcard.end():]
			
			text = text.replace("**", emph(label, True).lower())
			text = text.replace("*", emph(label, True))
		
		return text
	
	
	def indexed_document(self):
		if not self._indexed_document: self.create_index()
		return self._indexed_document
	
	
	def index_replace(self, the_match):
		return self.index_html(the_match.group(1))
	
	
	def alias_replace(self, the_match):
		replacement = the_match.group(0)
		if the_match.group(1) and the_match.group(1) in self.aliases:			
			replacement = self._path_delimiter.join(f'"{elem}"' for elem in self.aliases[the_match.group(1)][TextIndex._alias_path])
		return replacement
	
	
	def index_html(self, config_string=None):
		if not self._indexed_document: self.create_index()
		
		# Process any parameters in the index directive.
		if config_string:
			config_attrs = {
											TextIndex._prefix: '_index_id_prefix',
											TextIndex._see: '_see_label',
											TextIndex._also: '_see_also_label',
											TextIndex._headings: '_group_headings',
											TextIndex._run_in: '_should_run_in',
											TextIndex._emph_first: '_sort_emph_first',
											}
			for key, attr in config_attrs.items():
				param_match = re.search(rf"(?i){key}=(['\"])(.+?)\1", config_string)
				if param_match and param_match.group(2):
					setattr(self, attr, param_match.group(2))
		
		# Generate HTML.
		html = ""
		if len(self.entries) > 0:
			if self.depth > 1:
				if self.should_run_in:
					deepest = self.depth + 1
					self.inform(f"Deep index (>2 levels). Level {deepest} entries will be run-in to level {deepest - 1}. See docs to disable.", severity="warning")
				else:
					self.inform(f"Deep index (>2 levels). Consider reducing depth, or enable run-in (see docs).", severity="warning")
			
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
			self.inform(f"No index entries defined.", severity="warning")

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
			self.inform(f"Index might be too {'short' if ratio < low_bound else 'long'} compared to document: ratio is {ratio}% (ideal: {low_bound}–{high_bound}%).", severity="warning")
		else:
			self.inform(f"Good index size ratio to document: {ratio}% (ideal: {low_bound}–{high_bound}%).")
		
		return html
	
	
	def group_heading(self, letter, is_first=False):
		output = ""
		group_headings = self.group_headings_enabled
		if group_headings or not is_first:
			output += f'\t<dt class="group-separator{" group-heading" if group_headings else ""}">{letter if group_headings else "&nbsp;"}</dt>\n'
		return output
	
	
	def entry_html(self, entry):
		# Cross-refs (non-also), then ordered references, then parent's also-refs.
		refs_html = ""
		refs_output = False
		running_in = entry.parent and entry.parent.run_in_children()
		
		# Entry's see-references.
		has_xrefs = False
		xrefs_html = entry.render_cross_references()
		if xrefs_html != None:
			if running_in:
				refs_html += f" (<em>{self.see_label.lower()}</em> {xrefs_html})"
			else:
				refs_html += f"{TextIndex._category_separator}<em>{self.see_label.capitalize()}</em> {xrefs_html}"
			refs_output = True
			has_xrefs = True
		
		# Entry's references (locators).
		has_refs = False
		entry_refs_html = entry.render_references()
		if entry_refs_html != None:
			refs_html += (TextIndex._category_separator if refs_output else TextIndex._field_separator)
			refs_html += entry_refs_html
			refs_output = True
			has_refs = True
		
		run_in_children = entry.run_in_children()
		if run_in_children:
			delim = self._category_separator # if has_xrefs but not has_refs
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
		
		# Check whether we lack children and thus potentially need to inline our own see-also references.
		# This provides run-in style for such references.
		if (not entry.has_children() or run_in_children) and entry.has_also_refs():
			alsorefs_html = entry.render_also_references()
			if alsorefs_html != None:
				if running_in:
					refs_html += f" (<em>{self.see_also_label.lower()}</em> {alsorefs_html})"
				else:
					refs_html += f"{TextIndex._category_separator}<em>{self.see_also_label.capitalize()}</em> {alsorefs_html}"
				refs_output = True
		
		# Create our assembled entry's HTML.
		depth = entry.depth() + 1
		indent = max((2 * depth - 1), 1) * '\t'
		html = f'<span class="entry-heading">{emph(entry.label) if entry.label else ""}</span><span class="entry-references">{refs_html}</span>'
		if not running_in:
			html = f"{indent}<dt>{html}</dt>\n"
		
		# Handle subordinate indented elements.
		if not run_in_children:
			# Children, if indented.
			if len(entry.entries) > 0:
				html += f'{indent}<dd>\n{indent}\t<dl>\n'
				for child in self.sort_entries(entry.entries):
					html += self.entry_html(child)
				html += f'{indent}\t</dl>\n{indent}</dd>\n'
		
		# Parent's see-also cross-references.
		if entry.parent and entry.parent.has_also_refs() and not running_in:
			alsorefs_html = entry.parent.render_also_references()
			if alsorefs_html != None:
				html += f'{indent}<dt><span class="entry-references">'
				html += f"<em>{self.see_also_label.capitalize()}</em> {alsorefs_html}"
				html += '</span></dt>\n'		
				refs_output = True
		
		return html
	
	
	def sort_entries(self, entries):
		from operator import methodcaller
		return sorted(entries, key=methodcaller('sort_on'))
	
	
	def get_see_label(self):
		return self._see_label
	
	
	def get_see_also_label(self):
		return self._see_also_label
	
	
	def get_index_id_prefix(self):
		return self._index_id_prefix
	
	
	def get_group_headings_enabled(self):
		if isinstance(self._group_headings, bool):
			return self._group_headings
		return self._group_headings.lower() == "true"
	
	
	def get_should_run_in(self):
		if isinstance(self._should_run_in, bool):
			return self._should_run_in
		return self._should_run_in.lower() == "true"
	
	
	def get_sort_emph_first(self):
		if isinstance(self._sort_emph_first, bool):
			return self._sort_emph_first
		return self._sort_emph_first.lower() == "true"
	
	
	def set_see_label(self, val):
		self._see_label = val
		self._indexed_document = None
	
	
	def set_see_also_label(self, val):
		self._see_also_label = val
		self._indexed_document = None
	
	
	def set_index_id_prefix(self, val):
		self._index_id_prefix = val
		self._indexed_document = None
	
	
	def set_group_headings_enabled(self, val):
		if isinstance(val, str):
			val = (val.lower() == "true")
		elif not isinstance(val, bool):
			val = False
		self._group_headings = val
		self._indexed_document = None
	
	
	def set_should_run_in(self, val):
		if isinstance(val, str):
			val = (val.lower() == "true")
		elif not isinstance(val, bool):
			val = True
		self._should_run_in = val
		self._indexed_document = None
	
	
	def set_sort_emph_first(self, val):
		if isinstance(val, str):
			val = (val.lower() == "true")
		elif not isinstance(val, bool):
			val = True
		self._sort_emph_first = val
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
	group_headings_enabled = property(get_group_headings_enabled, set_group_headings_enabled)
	should_run_in = property(get_should_run_in, set_should_run_in)
	sort_emph_first = property(get_sort_emph_first, set_sort_emph_first)


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
		self.textindex = None
	
	
	def sort_on(self):
		return (self.sort_key if self.sort_key else emph(self.label, True)).lower()
	
	
	def add_reference(self, start_id, suffix=None, locator_emphasis=False):
		self.references.append({
														TextIndex._ref_type: TextIndex._reference,
														self.start_id: start_id,
														self.suffix: suffix,
														self.locator_emphasis: locator_emphasis
													})
	
	
	def add_cross_reference(self, ref_type, path):
		# Check this isn't a duplicate.
		if len(self.cross_references) > 0:
			for ref in self.cross_references:
				if ref[self.textindex._ref_type] == ref_type and ref[self.textindex._path] == path:
					return	
		self.cross_references.append({self.textindex._ref_type: ref_type, self.textindex._path: path})
	
	
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
	
	
	def has_children(self):
		return (len(self.entries) > 0)
	
	
	def has_also_refs(self):
		also_xrefs = False
		if len(self.cross_references) > 0:
			for ent in self.cross_references:
				if ent[TextIndex._ref_type] == TextIndex._also:
					also_xrefs = True
					break
		return also_xrefs
	
	
	def run_in_children(self):
		# Determines if this entry should be render its children in run-in style.
		# Top-level entries are at level 0, and are considered children of the index itself.
		# Depths 0 and 1 (top-level entries, and their sub-entries) are always indented.
		# Thereafter, for practical reasons, only the deepest level is run-in.
		# (Please don't make indexes deeper than root+2 levels though, for your readers' sake!)
		
		if self.textindex.should_run_in:
			my_depth = self.depth()
			return my_depth > 0 and my_depth == self.textindex.depth - 1
		return False
	
	
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
	
	
	def render_references(self):
		refs = []
		
		if len(self.references) > 0:
			if self.textindex.sort_emph_first:
				self.references.sort(key=lambda d: d[TextIndexEntry.locator_emphasis], reverse=True)
			loc_class = "locator"
			for i in range(len(self.references)):
				ref = self.references[i]
				locator_html = f'<a class="{loc_class}" href="#{self.textindex.index_id_prefix}{ref[TextIndexEntry.start_id]}" data-index-id="{ref[TextIndexEntry.start_id]}" data-index-id-elided="{ref[TextIndexEntry.start_id]}"></a>'
				if TextIndexEntry.end_id in ref:
					elided_end = elide_end(ref[TextIndexEntry.start_id], ref[TextIndexEntry.end_id])
					locator_html += TextIndex._range_separator
					locator_html += f'<a class="{loc_class}" href="#{self.textindex.index_id_prefix}{ref[TextIndexEntry.end_id]}" data-index-id="{ref[TextIndexEntry.end_id]}" data-index-id-elided="{elided_end}"></a>'
				suffix_applied = False
				if TextIndexEntry.suffix in ref and ref[TextIndexEntry.suffix]:
					locator_html += f'{ref[TextIndexEntry.suffix]}'
					suffix_applied = True
				if TextIndexEntry.end_suffix in ref and ref[TextIndexEntry.end_suffix]:
					locator_html += f'{" " if suffix_applied else ""}{ref[TextIndexEntry.end_suffix]}'
				if ref[TextIndexEntry.locator_emphasis]:
					locator_html = f"<em>{locator_html}</em>"
				
				refs.append(locator_html)
			
			if len(refs) > 0:
				return TextIndex._field_separator.join(refs)
		
		return None
	
	
	def render_cross_references(self):
		# See-type cross-references.
		refs = []
		
		if len(self.cross_references) > 0:
			self.sort_cross_refs()
			
			for i in range(len(self.cross_references)):
				ref = self.cross_references[i]
				if ref[TextIndex._ref_type] == TextIndex._see:
					refs.append(f'{TextIndex._path_separator.join(ref[TextIndex._path])}')
			if len(refs) > 0:
				return f"{TextIndex._refs_delimiter} ".join(refs)
			
		return None
	
	
	def render_also_references(self):
		# Also-type cross-references.
		refs = []
		
		if len(self.cross_references) > 0:
			self.sort_cross_refs()
			
			for i in range(len(self.cross_references)):
				ref = self.cross_references[i]
				if ref[TextIndex._ref_type] == TextIndex._also:
					refs.append(f'{TextIndex._path_separator.join(ref[TextIndex._path])}')
			if len(refs) > 0:
				return f"{TextIndex._refs_delimiter} ".join(refs)
			
		return None
	
	
	def sort_cross_refs(self):
		if len(self.cross_references) > 0:
			# First sort by path alphabetically.
			self.cross_references.sort(key=lambda d: ''.join(d[TextIndex._path]))
			# Then sort the see-refs first.
			self.cross_references.sort(key=lambda d: d[TextIndex._ref_type], reverse=True)
	
	
	def __str__(self):
		num_children = len(self.entries)
		path_str = TextIndex._path_delimiter.join(self.path_list()[:-1])
		return f"Entry: \"{self.label}\", depth {self.depth()} {'(' + path_str + TextIndex._path_delimiter +')' if path_str != '' else ''} [{num_children} child{'' if num_children == 1 else 'ren'}{', run-in' if self.run_in_children() else ', indented'}]"
	
	
	def __bool__(self):
		return True
	
	
	def __repr__(self):
		return self.__str__()
	
	
	def __len__(self):
		num_entries = 1
		for entry in self.entries:
			num_entries += len(entry)
		return num_entries
