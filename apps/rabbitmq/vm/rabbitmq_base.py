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
# Common definitions for RabbitMQ deployments.
#
################################################################################

from gce import *

def RabbitMQ_Node(
    name, role, sourceImage, startupScript, machineType='n1-standard-2'):
  return Compute.instance(
    name=name,
    machineType=machineType,
    disks=[
      Disk.boot(
        autoDelete=true,
        initializeParams=Disk.initializeParams(
          sourceImage=sourceImage,
        ),
      ),
    ],
    metadata=Metadata.create(
      items=[
        Metadata.startupScript(startupScript),
        Metadata.item('rabbitmq-role', role),
      ],
    ),
  )

def RabbitMQ_Cluster(
    sourceImage, startupScript,
    numRamNodes=4, ramNodeMachineType='n1-standard-2',
    numDiscNodes=3, discNodeMachineType='n1-standard-2'):
  assert numDiscNodes >= 1, 'numDiscNodes must be at least 1'

  ram_nodes = [
      RabbitMQ_Node(
        name='rabbitmq-ram-%d' % i,
        role='ram',
        sourceImage=sourceImage,
        startupScript=startupScript,
      ) for i in range(0, numRamNodes)]

  disc_nodes = [
      RabbitMQ_Node(
        name='rabbitmq-disc-%d' % i,
        role='disc',
        sourceImage=sourceImage,
        startupScript=startupScript,
      ) for i in range(0, numDiscNodes)]

  resources = ram_nodes + disc_nodes

  # Point each of the nodes towards the first disc node for discovery.
  for resource in resources:
    # Note: we can't use the syntax "resource.metadata.items.append" because
    # our dict-like object has the method "items()" which will shadow the field.
    resource.metadata['items'].append(
        Metadata.item('rabbitmq-server', disc_nodes[0].name))

  return resources
