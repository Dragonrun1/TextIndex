import os
import sys
import argparse
from textindex import textindex

parser = argparse.ArgumentParser(allow_abbrev=False)
parser.add_argument('--verbose', '-v', help="[optional] Enable verbose logging", action="store_true", default=False)
args=parser.parse_known_args()
file_path = "example.md"
verbose = (args[0].verbose == True)
if len(args) > 1:
	extra_args = args[1]
	if (len(extra_args) > 0):
		file_path = extra_args[0]

this_script_path = os.path.abspath(os.path.expanduser(sys.argv[0]))
file_path = os.path.join(os.path.dirname(this_script_path), file_path)

try:
	# Open and read file.
	file_path = os.path.abspath(file_path)
	input_file = open(file_path, 'r')
	file_contents = input_file.read()
	input_file.close()
	
	# Process index.
	index = textindex.TextIndex(file_contents)
	index.verbose = verbose
	file_contents = index.indexed_document()
	
	# Write out result to "-converted" file alongside original.
	basename, sep, ext = file_path.partition(".")
	output_filename = f"{basename}-converted{sep}{ext}"
	output_file = open(output_filename, 'w')
	output_file.write(file_contents)
	output_file.close()
	print(f"Wrote output file: {output_filename}")
 
except IOError as e:
	print(f"Error: {e}")
	sys.exit(1)
