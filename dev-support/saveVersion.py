#! /usr/bin/python

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# This file is used to generate package-info.java with an annotation that
# records the version, revision, user, date, url, and srcChecksum

import os
import sys
import re
import subprocess
import getpass
import time
import hashlib

def usage():
  print >>sys.stderr, "Usage: saveVersion.py <annotation> <version> <src_checksum_root_dir> <package> <build_dir>"
  print >>sys.stderr, "Eg:    saveVersion.py @HadoopVersionAnnotation 1.1.0 src org.apache.hadoop build"


# This template is what gets written to package-info.java.
# It is filled out by (annotation, version, revision, user, date, url,
# srcChecksum, package)

template_string = \
'''/*
 * Generated by saveVersion.py
 */
%s(version="%s", revision="%s",
  user="%s", date="%s", url="%s",
  srcChecksum="%s")
package %s;
'''

# Convert Windows paths with back-slashes into canonical Unix paths
# with forward slashes.  Unix paths are unchanged.  Mixed formats
# just naively have back-slashes converted to forward slashes.
def canonicalpath(path):
  return re.sub('\\\\','/',path)

# This is an implementation of md5sum-like functionality in pure python.
# The path name is output in canonical form to get the same aggregate
# checksum as Linux.
def md5sum(fname):
  block_size = 2**20
  f = open(os.path.normpath(fname), 'rb')  # open in binary mode to make sure EOLs don't get munged
  md5 = hashlib.md5()
  while True:
    data = f.read(block_size)
    if not data:
      break
    md5.update(data)
  f.close()
  return md5.hexdigest()

# Roughly emulate the Python 2.7 functionality of "subprocess.check_output()"
# by accepting a CLI vector [cmd, arg1, arg2, ...], and returning its stdout result,
# but without the "checking".  For use in lower version Python interpreters.
def subprocessOutput(args):
  # result = subprocess.check_output(args, shell=True) # requires py2.7
  process = subprocess.Popen(args, stdout=subprocess.PIPE)
  result = process.communicate()[0].strip()
  return result

# Strip surrounding quotes from a string object that carried its quotes with it.
def stripquotes(s):
  if (s[0] == '"' and s[-1] == '"') or (s[0] == "'" and s[-1] == "'") :
    return s[1:-1]
  elif (s[0] == '\\' and s[-1] == '"') :
    return s[1:-1]
  else:
    return s


def main(argv=None):
  if argv is None:
    argv = sys.argv[1:]
  if (len(argv) != 5) or (argv[0] == "--help") or (argv[0] == "-h"):
    usage()
    return -1

  annotation = argv[0]
  version = argv[1]
  src_checksum_root_dir = argv[2]
  package = argv[3]
  build_dir = argv[4]

  user = getpass.getuser()
  date = time.strftime("%a %b %d %H:%M:%S %Z %Y")  # simulate `date`

  os.chdir(os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), "..")))
  if os.path.isdir(".git"):
    revision = stripquotes(subprocessOutput(['git', 'log', '-1', '--pretty=format:"%H"']))
    origin = subprocessOutput(['git', 'config', '--get', 'remote.origin.url'])
    branch = subprocessOutput(['git', 'branch'])

    filter_current_branch = re.compile(r'^\* (.*)$', re.MULTILINE)
    current_branch = filter_current_branch.search(branch).group(1).strip()
    url = "%s on branch %s" % (origin, current_branch)
  else:
    svn_info = subprocessOutput(['svn', 'info'])
    filter_last_revision = re.compile(r'^Last Changed Rev: (.*)$', re.MULTILINE)
    revision = filter_last_revision.search(svn_info).group(1).strip()

    filter_url = re.compile(r'^URL: (.*)$', re.MULTILINE)
    url = filter_url.search(svn_info).group(1).strip()

  filter_java = re.compile(r'.+\.java$')
  file_list = []
  for root, dirs, files in os.walk(os.path.normpath(src_checksum_root_dir)):
    for name in files:
      if filter_java.match(name):
        canonical_name = canonicalpath(os.path.join(root, name))
        if not 'generated-sources' in canonical_name:
          file_list.append(canonical_name)

  # Sorting is done on unix-format names, case-folded, in order to get a platform-independent sort.
  file_list.sort(key=str.upper)
  file_count = len(file_list)
  hash = hashlib.md5()
  for name in file_list:
    file_hash_string = md5sum(name)
    hash.update(file_hash_string)

  srcChecksum = hash.hexdigest()

  target_dir = os.path.normpath(build_dir)
  if not os.path.exists(target_dir):
    os.makedirs(target_dir)

  target_file = os.path.join(target_dir, 'package-info.java')
  fout = open(target_file, "w")
  fout.write(template_string % (annotation, version, revision, user, date, url, srcChecksum, package))
  fout.close()

  print("Checksummed %s src/**.java files" % file_count)
  return 0

##########################
if __name__ == "__main__":
  sys.exit(main())