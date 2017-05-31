# Copyright 2015 IBM Corp.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


from ceilometer.compute.virt import inspector
from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class ZVMException(inspector.InspectorException):
    pass


def get_inst_name(instance):
    return getattr(instance, 'OS-EXT-SRV-ATTR:instance_name', None)


def get_inst_power_state(instance):
    return getattr(instance, 'OS-EXT-STS:power_state', None)
