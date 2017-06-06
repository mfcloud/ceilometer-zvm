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

    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_inspect_cpus(self, inst_name, inst_power_state, inspect_cpus):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        inspect_cpus.return_value = {'FAKEINST': {
            'guest_cpus': 1,
            'used_cpu_time_us': 7185838,
            'elapsed_cpu_time_us': 35232895,
            'min_cpu_count': 2,
            'max_cpu_limit': 10000,
            'samples_cpu_in_use': 0,
            'samples_cpu_delay': 0}}
        rdata = self._inspector.inspect_cpus(self._inst)
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        inspect_cpus.assert_called_once_with('FAKEINST')
        self.assertIsInstance(rdata, virt_inspector.CPUStats)
        self.assertEqual(rdata.number, 1)
        self.assertEqual(rdata.time, 7185838000)

    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_inspect_cpus_power_off(self, inst_name, inst_power_state,
                                    inspect_cpus):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x04
        self.assertRaises(virt_inspector.InstanceShutOffException,
                          self._inspector.inspect_cpus,
                          self._inst)
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        inspect_cpus.assert_not_called()

    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_inspect_cpus_not_exist(self, inst_name, inst_power_state,
                                    inspect_cpus):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        inspect_cpus.side_effect = sdkexception.ZVMVirtualMachineNotExist(
            msg='msg')
        self.assertRaises(virt_inspector.InstanceNotFoundException,
                          self._inspector.inspect_cpus,
                          self._inst)
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        inspect_cpus.assert_called_with('FAKEINST')

    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_inspect_cpus_other_exception(self, inst_name, inst_power_state,
                                    inspect_cpus):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        inspect_cpus.side_effect = sdkexception.SDKBaseException(
            msg='msg')
        self.assertRaises(virt_inspector.InstanceNoDataException,
                          self._inspector.inspect_cpus,
                          self._inst)
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        inspect_cpus.assert_called_with('FAKEINST')

    @mock.patch.object(sdkapi.SDKAPI, 'guest_get_power_state')
    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_inspect_cpus_null_data_shutdown(self, inst_name, inst_power_state,
                                  inspect_cpus, sdk_power_state):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        inspect_cpus.return_value = {}
        sdk_power_state.return_value = 'off'
        self.assertRaises(virt_inspector.InstanceShutOffException,
                          self._inspector.inspect_cpus,
                          self._inst)
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        inspect_cpus.assert_called_once_with('FAKEINST')

    @mock.patch.object(sdkapi.SDKAPI, 'guest_get_power_state')
    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_inspect_cpus_null_data_not_exist(self, inst_name,
                                  inst_power_state, inspect_cpus,
                                  sdk_power_state):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        inspect_cpus.return_value = {}
        sdk_power_state.side_effect = sdkexception.ZVMVirtualMachineNotExist(
            msg='msg')
        self.assertRaises(virt_inspector.InstanceNotFoundException,
                          self._inspector.inspect_cpus,
                          self._inst)
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        inspect_cpus.assert_called_once_with('FAKEINST')

    @mock.patch.object(sdkapi.SDKAPI, 'guest_get_power_state')
    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_inspect_cpus_null_data_active(self, inst_name, inst_power_state,
                                  inspect_cpus, sdk_power_state):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        inspect_cpus.return_value = {}
        sdk_power_state.return_value = 'on'
        self.assertRaises(virt_inspector.InstanceNoDataException,
                          self._inspector.inspect_cpus,
                          self._inst)
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        inspect_cpus.assert_called_once_with('FAKEINST')

    @mock.patch.object(sdkapi.SDKAPI, 'guest_get_power_state')
    @mock.patch.object(sdkapi.SDKAPI, 'guest_inspect_cpus')
    @mock.patch.object(zvmutils, 'get_inst_power_state')
    @mock.patch.object(zvmutils, 'get_inst_name')
    def test_inspect_cpus_null_data_unknown_exception(self, inst_name,
                                  inst_power_state, inspect_cpus,
                                  sdk_power_state):
        inst_name.return_value = 'FAKEINST'
        inst_power_state.return_value = 0x01
        inspect_cpus.return_value = {}
        sdk_power_state.side_effect = sdkexception.SDKBaseException(
            msg='msg')
        self.assertRaises(virt_inspector.InstanceNoDataException,
                          self._inspector.inspect_cpus,
                          self._inst)
        inst_name.assert_called_once_with(self._inst)
        inst_power_state.assert_called_once_with(self._inst)
        inspect_cpus.assert_called_once_with('FAKEINST')
