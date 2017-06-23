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


from ceilometer.compute.virt import inspector as virt_inspector
from ceilometer.i18n import _
from ceilometer_zvm.compute.virt.zvm import utils as zvmutils
from oslo_log import log
from oslo_utils import units
from zvmsdk import api as sdkapi
from zvmsdk import exception as sdkexception


LOG = log.getLogger(__name__)


class ZVMInspector(virt_inspector.Inspector):

    def __init__(self):
        self._sdkapi = sdkapi.SDKAPI()

    def inspect_cpus(self, instance):
        cpu_data = self._inspect_inst_data(instance, 'cpu')

        # Construct the final result
        cpu_number = cpu_data['guest_cpus']
        used_cpu_time = (cpu_data['used_cpu_time_us'] * units.k)
        return virt_inspector.CPUStats(number=cpu_number,
                                       time=used_cpu_time)

    def inspect_memory_usage(self, instance, duration=None):
        mem_data = self._inspect_inst_data(instance, 'mem')

        # Construct the final result
        used_mem_mb = mem_data['used_mem_kb'] / units.Ki
        return virt_inspector.MemoryUsageStats(usage=used_mem_mb)

    def _inspect_inst_data(self, instance, inspect_type):
        inspect_data = {}
        inst_name = zvmutils.get_inst_name(instance)
        msg_shutdown = _("Can not get vm info in shutdown state "
                    "for %s") % inst_name
        msg_notexist = _("Can not get vm info for %s, vm not exist"
                         ) % inst_name
        msg_nodata = _("Failed to get vm info for %s") % inst_name
        # zvm inspector can not get instance info in shutdown stat
        if zvmutils.get_inst_power_state(instance) == 0x04:
            raise virt_inspector.InstanceShutOffException(msg_shutdown)
        try:
            if inspect_type == 'cpu':
                inspect_data = self._sdkapi.guest_inspect_cpus(inst_name)
            else:
                inspect_data = self._sdkapi.guest_inspect_mem(inst_name)
        except sdkexception.ZVMVirtualMachineNotExist:
            raise virt_inspector.InstanceNotFoundException(msg_notexist)
        except Exception:
            raise virt_inspector.InstanceNoDataException(msg_nodata)

        # Check the inst data is in the returned result
        index_key = inst_name.upper()
        if index_key not in inspect_data:
            # Check the reason: shutdown or not exist or other error
            try:
                vm_state = self._sdkapi.guest_get_power_state(inst_name)
            except sdkexception.ZVMVirtualMachineNotExist:
                raise virt_inspector.InstanceNotFoundException(msg_notexist)
            except Exception:
                raise virt_inspector.InstanceNoDataException(msg_nodata)
            if vm_state == 'off':
                raise virt_inspector.InstanceShutOffException(msg_shutdown)
            else:
                raise virt_inspector.InstanceNoDataException(msg_nodata)
        else:
            return inspect_data[index_key]

    def inspect_vnics(self, instance):
        pass
