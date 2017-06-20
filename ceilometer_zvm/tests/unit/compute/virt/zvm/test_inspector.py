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


import mock
import unittest

from ceilometer.compute.virt import inspector as virt_inspector
from ceilometer_zvm.compute.virt.zvm import inspector as zvminspector
from ceilometer_zvm.compute.virt.zvm import utils as zvmutils
from zvmsdk import api as sdkapi
from zvmsdk import exception as sdkexception


class TestZVMInspector(unittest.TestCase):

    def setUp(self):
        unittest.TestCase.setUp(self)
        self._inspector = zvminspector.ZVMInspector()
        self._inst = mock.MagicMock()
        self._cpu_dict = {
            'guest_cpus': 1,
            'used_cpu_time_us': 7185838,
            'elapsed_cpu_time_us': 35232895,
            'min_cpu_count': 2,
            'max_cpu_limit': 10000,
            'samples_cpu_in_use': 0,
            'samples_cpu_delay': 0}
        self._mem_dict = {'used_mem_kb': 390232,
                          'max_mem_kb': 3097152,
                          'min_mem_kb': 0,
                          'shared_mem_kb': 5222192}

    @mock.patch.object(zvminspector.ZVMInspector, "_inspect_cpumem_data")
    def test_inspect_cpus(self, inspect_cpumem):
        inspect_cpumem.return_value = self._cpu_dict
        rdata = self._inspector.inspect_cpus(self._inst)
        inspect_cpumem.assert_called_once_with(self._inst, 'cpu')
        self.assertIsInstance(rdata, virt_inspector.CPUStats)
        self.assertEqual(rdata.number, 1)
        self.assertEqual(rdata.time, 7185838000)

    @mock.patch.object(zvminspector.ZVMInspector, "_inspect_cpumem_data")
    def test_inspect_memory_usage(self, inspect_cpumem):
        inspect_cpumem.return_value = self._mem_dict
        rdata = self._inspector.inspect_memory_usage(self._inst)
        inspect_cpumem.assert_called_once_with(self._inst, 'mem')
        self.assertIsInstance(rdata, virt_inspector.MemoryUsageStats)
        self.assertEqual(rdata.usage, 381)

    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_mem')
    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_private_inspect_cpumem_type_cpu(self, inst_name, inst_power_state,
                                             sdk_inspect_cpu, sdk_inspect_mem):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        sdk_inspect_cpu.return_value = {'FAKEINST': self._cpu_dict}
        rdata = self._inspector._inspect_cpumem_data(self._inst, 'cpu')
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        sdk_inspect_cpu.assert_called_once_with('FAKEINST')
        sdk_inspect_mem.assert_not_called()
        self.assertDictEqual(rdata, self._cpu_dict)

    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_mem')
    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_private_inspect_cpumem_type_mem(self, inst_name, inst_power_state,
                                             sdk_inspect_cpu, sdk_inspect_mem):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        sdk_inspect_mem.return_value = {'FAKEINST': self._mem_dict}
        rdata = self._inspector._inspect_cpumem_data(self._inst, 'mem')
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        sdk_inspect_mem.assert_called_once_with('FAKEINST')
        sdk_inspect_cpu.assert_not_called()
        self.assertDictEqual(rdata, self._mem_dict)

    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_private_inspect_cpumem_power_off(self, inst_name,
                                              inst_power_state,
                                              sdk_inspect_cpus):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x04
        self.assertRaises(virt_inspector.InstanceShutOffException,
                          self._inspector._inspect_cpumem_data,
                          self._inst, 'cpu')
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        sdk_inspect_cpus.assert_not_called()

    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_private_inspect_cpumem_not_exist(self, inst_name,
                                              inst_power_state,
                                              sdk_inspect_cpus):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        sdk_inspect_cpus.side_effect = sdkexception.ZVMVirtualMachineNotExist(
            msg='msg')
        self.assertRaises(virt_inspector.InstanceNotFoundException,
                          self._inspector._inspect_cpumem_data,
                          self._inst, 'cpu')
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        sdk_inspect_cpus.assert_called_with('FAKEINST')

    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_private_inspect_cpumem_other_exception(self, inst_name,
                                                    inst_power_state,
                                                    sdk_inspect_cpus):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        sdk_inspect_cpus.side_effect = sdkexception.SDKBaseException(
            msg='msg')
        self.assertRaises(virt_inspector.InstanceNoDataException,
                          self._inspector._inspect_cpumem_data,
                          self._inst, 'cpu')
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        sdk_inspect_cpus.assert_called_with('FAKEINST')

    @mock.patch.object(sdkapi.SDKAPI, 'guest_get_power_state')
    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_private_inspect_cpumem_null_data_shutdown(self, inst_name,
                                                       inst_power_state,
                                                       sdk_inspect_cpus,
                                                       sdk_power_state):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        sdk_inspect_cpus.return_value = {}
        sdk_power_state.return_value = 'off'
        self.assertRaises(virt_inspector.InstanceShutOffException,
                          self._inspector._inspect_cpumem_data,
                          self._inst, 'cpu')
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        sdk_inspect_cpus.assert_called_once_with('FAKEINST')

    @mock.patch.object(sdkapi.SDKAPI, 'guest_get_power_state')
    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_private_inspect_cpumem_null_data_not_exist(self, inst_name,
                                  inst_power_state, sdk_inspect_cpus,
                                  sdk_power_state):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        sdk_inspect_cpus.return_value = {}
        sdk_power_state.side_effect = sdkexception.ZVMVirtualMachineNotExist(
            msg='msg')
        self.assertRaises(virt_inspector.InstanceNotFoundException,
                          self._inspector._inspect_cpumem_data,
                          self._inst, 'cpu')
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        sdk_inspect_cpus.assert_called_once_with('FAKEINST')

    @mock.patch.object(sdkapi.SDKAPI, 'guest_get_power_state')
    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_private_inspect_cpumem_null_data_active(self, inst_name,
                                                     inst_power_state,
                                                     sdk_inspect_cpus,
                                                     sdk_power_state):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        sdk_inspect_cpus.return_value = {}
        sdk_power_state.return_value = 'on'
        self.assertRaises(virt_inspector.InstanceNoDataException,
                          self._inspector._inspect_cpumem_data,
                          self._inst, 'cpu')
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        sdk_inspect_cpus.assert_called_once_with('FAKEINST')

    @mock.patch.object(sdkapi.SDKAPI, 'guest_get_power_state')
    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_private_inspect_cpumem_null_data_unknown_exception(self,
            inst_name, inst_power_state, sdk_inspect_cpus, sdk_power_state):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        sdk_inspect_cpus.return_value = {}
        sdk_power_state.side_effect = sdkexception.SDKBaseException(
            msg='msg')
        self.assertRaises(virt_inspector.InstanceNoDataException,
                          self._inspector._inspect_cpumem_data,
                          self._inst, 'cpu')
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        sdk_inspect_cpus.assert_called_once_with('FAKEINST')
