#
# Script to combine web page templates with content pages for publishing to
# Github pages. This first pass is rough and should be updated to allow for
# variable expansion recursively.
#

import os
import re
import shutil
import sys

start_path = os.getcwd()
output_path = "_site"
pattern = re.compile('(.*){{\\s*([.\\w]*)\\s*}}(.*)')
dirs_to_copy = ['css', 'images']

#
# Checks the current line for template variables and expands them. Variables
# should have been read into the attr dictionary. The expanded contents will
# be written to outfile. The content variable is handled specially because it
# gets expanded into the entire contents of a content page. The contents 
# variable therefore contains a file pointer to the contents file, so those
# lines can be written in place.
#
def write_expanded_line(line, attrs, outfile, content_fh):
        m = pattern.match(line)
        if m:
            if m.group(2) == "content":
                outfile.write("<!-- marker -->\n")
                for content in content_fh:
                    outfile.write(content)
            else:
                attr_name = m.group(2)
                if attr_name not in attrs:
                    sys.stderr.write(f"attribute '{attr_name}' not in content file.\n")
                    outfile.write("*** ERROR ***")
                    sys.exit()
                replacement = m.group(1) + attrs[attr_name] + m.group(3)
                line = re.sub(pattern, replacement, line)
                outfile.write(line)
        else:   # Nothing to expand, just write the line as is.
            outfile.write(line)


#
# Expands the specified content file in filename by pulling in the lines from a
# template file. The template file should be named in the preamble of the
# content file.
#
def expand_file(filename):
    processing_header = False
    attrs = {}

    # TODO: do error checking here.
    in_fh = open(filename)

    
    target_file = filename.replace(start_path, output_path)
    dir_name = os.path.dirname(target_file)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)
    out_fh = open(target_file, "w")

    for line in in_fh:
        if line.startswith("---"):
            if processing_header:
                processing_header = False
            else:
                processing_header = True
            continue

        if processing_header:
            line = line.rstrip('\n')
            attr_name, attr_val = line.split(':', 2)
            attr_name = attr_name.strip()
            attr_val = attr_val.strip()
            attrs[attr_name] = attr_val
        else:
            if "layout" not in attrs:
                sys.stderr.write(f"no layout attribute in {filename}, generating raw file\n")
                out_fh.write("".join(contents))
                break
            layout_file = os.path.join("_layouts", attrs['layout'] + ".html")
            with open(layout_file) as layout_in:
                for layout_line in layout_in:
                    write_expanded_line(layout_line, attrs, out_fh, in_fh)
    in_fh.close()
    out_fh.close()


def walk_path(start_path):

    for entry in os.listdir(start_path):

        # Recurse into directories.
        if os.path.isdir(entry):
            if entry == "tmp":
                continue
            if entry[0] == "." or entry[0] == "_":
                continue
            else:
                print(f" recursing into {entry}")
                walk_path(os.path.join(start_path, entry))

        # Process html files.
        else:
            root, extension = os.path.splitext(entry)
            if extension == ".html" or extension == ".htm":
                print(f"processing {entry}")
                expand_file(os.path.join(start_path, entry))


if __name__ == "__main__":
    if not os.path.isdir(output_path):
        os.makedirs(output_path)
    walk_path(start_path)
    for dir_name in dirs_to_copy:
        shutil.copytree(dir_name, os.path.join(output_path, dir_name), dirs_exist_ok=True)

