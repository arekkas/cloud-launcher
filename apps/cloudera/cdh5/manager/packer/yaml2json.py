#!/usr/bin/python
#
# Copyright 2014 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
################################################################################
#
# Converts a YAML file to a JSON format, to be consumed by Packer.
#
################################################################################

import json
import yaml
import sys


def main(argv):
  if len(argv) < 2:
    sys.stderr.write('Syntax: %s [yaml-file]\n' % argv[0])
    sys.exit(1)

  with open(argv[1]) as yaml_input:
    data = yaml.safe_load(yaml_input)
    print json.dumps(data, indent=2)


if __name__ == '__main__':
  main(sys.argv)
