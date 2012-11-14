#!/bin/sh

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


# This file is used to generate the BuildStamp.java class that
# records the user, url, revision and timestamp.
unset LANG
unset LC_CTYPE
if [[ `which md5sum` != "" ]]; then
  # linux
  export MD5SUM="md5sum"
elif [[ `which md5` != "" ]]; then
  # mac
  export MD5SUM="md5 -r"
fi

version=$1
build_dir=$2
user=`whoami`
date=`date`
if [ -d .git ]; then
  revision=`git log -1 --pretty=format:"%H"`
  origin=`git config --get remote.origin.url`
  branch=`git branch | sed -n -e 's/^* //p'`
  url="$origin on branch $branch"
else
  revision=`svn info | sed -n -e 's/Last Changed Rev: \(.*\)/\1/p'`
  url=`svn info | sed -n -e 's/URL: \(.*\)/\1/p'`
fi
srcChecksum=`find src -name '*.java' | LC_ALL=C sort -f | xargs $MD5SUM | $MD5SUM | cut -d ' ' -f 1`
file_count=`find src -name '*.java' | LC_ALL=C sort -f | wc -l`

mkdir -p $build_dir/src/org/apache/hadoop
cat << EOF | \
  sed -e "s/VERSION/$version/" -e "s/USER/$user/" -e "s/DATE/$date/" \
      -e "s|URL|$url|" -e "s/REV/$revision/" -e "s/SRCCHECKSUM/$srcChecksum/" \
      > $build_dir/src/org/apache/hadoop/package-info.java
/*
 * Generated by src/saveVersion.sh
 */
@HadoopVersionAnnotation(version="VERSION", revision="REV", 
                         user="USER", date="DATE", url="URL",
                         srcChecksum="SRCCHECKSUM")
package org.apache.hadoop;
EOF

echo "Checksummed $file_count src/**.java files"