# Generate InSpec tests for basic files.
from os.path import join as get_path_of
from os.path import isdir, abspath, dirname
from os import walk as all_files_in
from os import listdir as ls
from hashlib import sha256 as sha2sum
name = 'check_files'
title = 'Docker volume file tests'
location = '{}/../../files/DockerVolumes/'.format(abspath(dirname(__file__)))
description = "Validity checks for files in {}".format(location)
control_header = \
'''control '{}' do
  impact 1
  title {}
  desc {}'''.format(name, title, description)
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
    return file_output.format(
        get_path_of(*args),
        sha2sum(open(get_path_of(*args)).read().encode()).hexdigest(),
        '{', '}'
    )

output = control_header
def describe_folder(folder):
    parent_test = folder_output.format(folder, '{', '}')
    output = ''
    for path in ls(folder):
        try:
            output += describe_file(folder + path)
        except IsADirectoryError:
            output += describe_folder(folder + path)
    return parent_test + output

output += describe_folder(location)
output += control_footer
print(output)
