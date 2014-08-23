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
# Queries Google Compute Engine and updates the local cache of GCP info.

# System imports
import argparse
import httplib2
import json
import logging
import os
import re
import urlparse
import sys

# Google Cloud API imports
from apiclient.discovery import build
from apiclient import errors
from apiclient import http
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client import gce
from oauth2client import tools
from oauth2client.tools import run_flow


API_VERSION = 'v1'
GCE_URL = 'https://www.googleapis.com/compute/%s/projects/' % (API_VERSION)
GCE_SCOPE = 'https://www.googleapis.com/auth/compute'


class GceService(object):

  def __init__(self, flags):
    self.__flags = flags

    # Perform OAuth 2.0 authorization.
    project_dir = os.path.join(
        os.getenv('HOME'), 'cloud', 'projects', flags.project)
    client_secrets = os.path.join(project_dir, 'client_secrets.json')
    oauth2_storage = os.path.join(project_dir, 'oauth2.dat')
    flow = flow_from_clientsecrets(client_secrets, scope=GCE_SCOPE)
    storage = Storage(oauth2_storage)
    credentials = storage.get()

    if credentials is None or credentials.invalid:
      credentials = run_flow(flow, storage, flags)
    self.http = credentials.authorize(httplib2.Http())
    self.compute = build('compute', API_VERSION)


def WriteJsonToFile(json_obj, filename):
  print 'Updating %s ...' % filename
  json_str = json.dumps(json_obj, indent=2, separators=(',', ': '), sort_keys=True)
  with open(filename, 'w') as output:
    output.write('%s\n' % json_str)


def UpdateVmImages(gce, flags):
  vm_images = {}
  vm_image_projects = (
      'centos-cloud', 'coreos-cloud', 'debian-cloud', 'google-containers',
      'opensuse-cloud', 'rhel-cloud', 'suse-cloud'
  )
  for project in vm_image_projects:
    images = gce.compute.images().list(project=project).execute(http=gce.http)
    for item in images['items']:
      if project not in vm_images:
        vm_images[project] = {}

      if 'images' not in vm_images[project]:
        vm_images[project]['images'] = []

      shortname = os.path.basename(urlparse.urlparse(item['selfLink']).path)
      vm_images[project]['images'].append(shortname)

  def LatestImage(images, date_pattern='-v[0-9]{8}$'):
    if 'pseudo' not in vm_images[project]:
      vm_images[project]['pseudo'] = {}
    vm_image_latest_dst = images[-1]
    vm_image_latest_src = re.sub(date_pattern, '-latest', vm_image_latest_dst)
    return (vm_image_latest_src, vm_image_latest_dst)

  for project in vm_images:
    images = vm_images[project].get('images', [])
    if len(images) == 0:
      continue

    if project == 'coreos-cloud':
      for substr in ('alpha', 'beta', 'stable'):
        image_sublist = filter(lambda image: substr in image, images)
        src, dst = LatestImage(image_sublist, '-[0-9]*-[0-9]-[0-9]-v[0-9]{8}$')
        vm_images[project]['pseudo'][src] = dst
    elif project == 'debian-cloud':
      backports = filter(lambda image: 'backports' in image, images)
      not_backports = filter(lambda image: 'backports' not in image, images)
      for image_sublist in (backports, not_backports):
        src, dst = LatestImage(image_sublist)
        vm_images[project]['pseudo'][src] = dst
    else:
      src, dst = LatestImage(images)
      vm_images[project]['pseudo'][src] = dst

  WriteJsonToFile(vm_images, 'vm_images.json')


def UpdateZones(gce, flags):
  zones = gce.compute.zones().list(project=flags.project).execute(http=gce.http)
  # TODO(mbrukman): clean up the zones output.
  WriteJsonToFile(zones, 'zones.json')


def main(argv):
  parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])

  parser.add_argument('--project', dest='project', required=True,
                      help='Project name')

  parser.add_argument('--debug', dest='debug', default=False,
                      action='store_true',
                      help='Whether to output debug info')

  parser.add_argument('--logging', dest='logging', default='',
                      choices=('', 'info', 'warning', 'error'),
                      help='Logging level to enable')

  flags = parser.parse_args(argv[1:])

  LOGGING = {
    '': None,
    'info': logging.INFO,
    'WARNING': logging.WARNING,
    'error': logging.ERROR,
  }
  logging.basicConfig(level=LOGGING[flags.logging])

  gce = GceService(flags)
  UpdateVmImages(gce, flags)
	# TODO(mbrukman): enable zone list caching once we define concise format.
  # UpdateZones(gce, flags)
  print 'Done.'


if __name__ == '__main__':
  main(sys.argv)
