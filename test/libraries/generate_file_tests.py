# Generate InSpec tests for basic files.
from os.path import join as get_path_of
from os.path import isdir, abspath, dirname
from os import walk as all_files_in
from os import listdir as ls
from hashlib import sha256 as sha2sum
from sys import argv
name = 'check_files'
title = 'Docker volume file tests'
try:
    location = argv[1]
except IndexError:
    location = get_path_of(
        abspath(dirname(__file__)),
        '..',
        '..',
        'files',
        'DockerVolumes'
    )
if not isdir(location):
    print(location, "must be a directory!")
    exit(1)
description = "Validity checks for files in {}".format(location)
control_header = \
'''control '{}' do
  impact 1
  title '{}'
  desc '{}' '''.format(name, title, description)
control_footer = '\nend\n'
folder_output='''
  describe file('{}') do
    it {} should be_directory {}
  end'''
file_output = '''
  describe file("{0}") do
    it {2} should be_file {3}
    its('sha256sum') {2} should cmp '{1}' {3}
  end'''
def describe_file(*args):
    """Create a describe test for a particular file."""
    print("decoding file at", get_path_of(*args))
    try:
        return file_output.format(
            get_path_of(*args),
            sha2sum(
                open(
                    get_path_of(*args), 'r'
                ).read().encode()
            ).hexdigest(),
            '{', '}'
        )
    except UnicodeDecodeError:
        return file_output.format(
            get_path_of(*args),
            sha2sum(
                open(
                    get_path_of(*args), 'rb'
                ).read().encode()
            ).hexdigest(),
            '{', '}'
        )

output = control_header
def describe_folder(folder):
    parent_test = folder_output.format(folder, '{', '}')
    output = ''
    for path in ls(folder):
        try:
            output += describe_file(get_path_of(folder, path))
        except IsADirectoryError:
            try:
                output += describe_folder(get_path_of(folder, path))
            except FileNotFoundError:
                # It literally makes no sense for there to be a FileNotFoundError
                # within this section.
                pass
    return parent_test + output

output += describe_folder(location)
output += control_footer
print(output)
