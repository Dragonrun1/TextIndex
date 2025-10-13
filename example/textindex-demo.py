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

import argparse
import os
import sys

from src.textindex import textindex

parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument(
    "--verbose",
    "-v",
    help="[optional] Enable verbose logging",
    action="store_true",
    default=False,
)
args = parser.parse_known_args()
file_path = "example.md"
conc_path = "example-concordance.tsv"
verbose = args[0].verbose == True

this_script_path = os.path.abspath(os.path.expanduser(sys.argv[0]))
file_path = os.path.join(os.path.dirname(this_script_path), file_path)
conc_path = os.path.join(os.path.dirname(this_script_path), conc_path)

if len(args) > 1:
    extra_args = args[1]
    if len(extra_args) > 0:
        file_path = extra_args[0]

try:
    # Open and read file.
    file_path = os.path.abspath(file_path)
    input_file = open(file_path, "r")
    file_contents = input_file.read()
    input_file.close()

    # Process index.
    index = textindex.TextIndex(file_contents)
    index.verbose = verbose
    index.convert_latex_index_commands()
    index.load_concordance_file(os.path.abspath(conc_path))
    file_contents = index.indexed_document()

    # Write out result to "-converted" file alongside original.
    basename, sep, ext = file_path.partition(".")
    output_filename = f"{basename}-converted{sep}{ext}"
    output_file = open(output_filename, "w")
    output_file.write(file_contents)
    output_file.close()
    print(f"Wrote output file: {output_filename}")

    if False:
        # Write out concorded intermediate file for inspection.
        output_filename = f"{basename}-intermediate{sep}{ext}"
        output_file = open(output_filename, "w")
        output_file.write(index.intermediate_document)
        output_file.close()

except IOError as e:
    print(f"Error: {e}")
    sys.exit(1)
