#!/usr/bin/env python3

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

import argparse
import sys
from pathlib import Path

from textindex import textindex

# -----------------------------
# Parse command-line arguments
# -----------------------------
parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument(
    "--verbose",
    "-v",
    help="[optional] Enable verbose logging",
    action="store_true",
    default=False,
)
parser.add_argument(
    "input_file",
    nargs="?",
    default="example.md",
    help="[optional] Markdown file to process",
)
args = parser.parse_args()

verbose = args.verbose

# -----------------------------
# Determine paths relative to this script
# -----------------------------
script_path = Path(__file__).resolve()
script_dir = script_path.parent

# Input Markdown file
file_path = script_dir / args.input_file

# Concordance / TOML configuration file
conc_path = script_dir / "textindex-config.toml"

# Output filename derived from input
output_filename = script_dir / f"{file_path.stem}-converted{file_path.suffix}"

# -----------------------------
# Check files exist
# -----------------------------
if not file_path.is_file():
    print(f"Error: Input file not found: {file_path}")
    sys.exit(1)

if not conc_path.is_file():
    print(f"Error: TOML configuration not found: {conc_path}")
    sys.exit(1)

# -----------------------------
# Process the document
# -----------------------------
try:
    file_contents = file_path.read_text(encoding="utf-8")

    index = textindex.TextIndex(file_contents)
    index.verbose = verbose
    index.convert_latex_index_commands()
    index.load_concordance_file(str(conc_path))
    file_contents = index.indexed_document()

    output_filename.write_text(file_contents, encoding="utf-8")

    print(f"Wrote output file: {output_filename}")

except IOError as e:
    print(f"Error: {e}")
    sys.exit(1)
