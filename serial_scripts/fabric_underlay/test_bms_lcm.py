import time
import test
from bms_fixture import BMSFixture
from tcutils.wrappers import preposttest_wrapper
from common.contrail_fabric.base import BaseFabricTest
from physical_router_fixture import PhysicalRouterFixture
from physical_device_fixture import PhysicalDeviceFixture

class TestBmsLcm(BaseFabricTest):
    def setUp(self):
        for device_name, device_dict in self.inputs.physical_routers_data.items():
            if device_dict['role'] == 'spine':
                self.rb_roles[device_name] = ['DC-Gateway','Route-Reflector']
        super(TestBmsLcm, self).setUp()

    def is_test_applicable(self):
        result, msg = super(TestBmsLcm, self).is_test_applicable()
        if result:
            msg = 'ironic service is not enabled'
            if self.inputs.is_ironic_enabled:
                return (True, None)
        return False, msg

    def check_ping_from_mx(self):
        internal_vip = self.inputs.internal_vip
        devices = self.inputs.physical_routers_data.keys()
        for device in self.inputs.physical_routers_data.iteritems():
            router_params = device[1]
            if router_params['role'] == 'spine':
               phy_router_fixture = self.useFixture(PhysicalRouterFixture(
                            router_params['name'], router_params['control_ip'],
                            model="mx",
                            vendor=router_params['vendor'],
                            asn=router_params['asn'],
                            ssh_username=router_params['ssh_username'],
                            ssh_password=router_params['ssh_password'],
                            mgmt_ip=router_params['control_ip'],
                            do_cleanup=False,
                            connections=self.connections))

               mx_handle = phy_router_fixture.get_connection_obj('juniper',
                    host=router_params['control_ip'],
                    username=router_params['ssh_username'],
                    password=router_params['ssh_password'],
                    logger=[self.logger])
               cmd = "ping %s wait 1"%internal_vip
               output = mx_handle.handle.cli(cmd)
               self.logger.debug(output)
               cmd = "run show bgp summary | display xml rpc"
               output = mx_handle.handle.cli(cmd)
               self.logger.debug(output)

    def bms_delete_nodes(self,bms_name=None,all_bms=False):
        node_list = self.connections.ironic_h.obj.node.list()
        for node in node_list:
            self.connections.ironic_h.obj.node.delete(node.uuid)

    def bms_node_add_delete(self,bms_type=None):
        '''
          Description: Create BMS ironic node
          Test steps:

          Maintainer: vageesant@juniper.net
        '''
        bms_lcm_config = self.inputs.bms_lcm_config
        bms_nodes = self.inputs.bms_data
        base_kernel_image = bms_lcm_config["deploy_kernel"]
        base_ramdisk_image = bms_lcm_config["deploy_ramdisk"]
        single_interface_bms_nodes = []
        lag_interface_bms_nodes    = []
        multi_homing_interface_bms_nodes = []

        bms_nodes_filtered = []
        for k,v in bms_nodes.iteritems():
              v['node_name'] = k
              if len(v['interfaces']) == 1 :
                 single_interface_bms_nodes.append(v)
              elif v['interfaces'][0]['tor'] != v['interfaces'][1]['tor']:
                 multi_homing_interface_bms_nodes.append(v)
              elif v['interfaces'][0]['tor'] == v['interfaces'][1]['tor']:
                 lag_interface_bms_nodes.append(v)

        bms_nodes_filtered = []

        if bms_type == "all":
           bms_nodes_filtered.extend(single_interface_bms_nodes)
           bms_nodes_filtered.extend(lag_interface_bms_nodes)
           bms_nodes_filtered.extend(multi_homing_interface_bms_nodes)
        elif bms_type == 'link_aggregation':
           bms_nodes_filtered = lag_interface_bms_nodes
        elif bms_type == 'single_interface':
           bms_nodes_filtered = single_interface_bms_nodes
        else:
           bms_nodes_filtered = multi_homing_interface_bms_nodes

        if len(bms_nodes_filtered) == 0:
           self.logger.debug("No Valid BMS Node available for the scenario: %s"%bms_type)
           return

        self.bms_fixture = self.useFixture(BMSFixture(self.connections,bms_nodes_filtered[0]['node_name'],is_ironic_node=True))
        base_kernel_uuid  = self.bms_fixture.connections.nova_h.get_image(base_kernel_image)['id']
        base_ramdisk_uuid = self.bms_fixture.connections.nova_h.get_image(base_ramdisk_image)['id']

        for bms_node in bms_nodes_filtered:
            self.bms_fixture = self.useFixture(BMSFixture(self.connections,bms_node['node_name'],is_ironic_node=True))
            driver_info = bms_node["driver_info"]
            properties  = bms_node['properties']
            driver_info['deploy_ramdisk']     = base_ramdisk_uuid
            driver_info['deploy_kernel']      = base_kernel_uuid

            interfaces = bms_node['interfaces']
            port_list = []
            for interface in interfaces:
                local_link_connection = {}
                local_link_connection['mac_addr']    = interface['host_mac']
                local_link_connection['switch_info'] = interface['tor']
                local_link_connection['switch_id']   = interface['switch_id']
                local_link_connection['pxe_enabled'] = interface['pxe_enabled']
                local_link_connection['port_id']     = interface['tor_port']
                port_list.append(local_link_connection)

            self.bms_fixture.create_bms_node(ironic_node_name=bms_node['node_name'],port_list=port_list,driver_info=driver_info,properties=properties)
            self.bms_fixture.set_bms_node_state("available")
        self.logger.debug(self.bms_fixture.connections.ironic_h.obj.node.list())
        #self.bms_fixture.delete_ironic_node()
        #print self.bms_fixture.ironic_h.obj.node.list()

    @preposttest_wrapper
    def test_bms_single_interface(self):
        '''
        Description: Test BMS LCM scenario for single interface BMS node
        Test Steps:
           1. Delete all existing BMS nodes and create only one ironic node - the host which has single interface
           2. Update SG to allow ping/traffic between BMS VM and regular VM
           3. Reconfigure TFTP Block size and ip link MTU
           4. Bringup one BMS LCM instance and one VM.Verify ping between VM and BMS VM instance works.
        Maintainer: vageesant@juniper.net
        '''
        self.bms_delete_nodes()
        self.bms_node_add_delete(bms_type="single_interface")
        time.sleep(60)
        self.bms_vm_add_delete(bms_count=1)

    @preposttest_wrapper
    def test_bms_multi_homing(self):
        '''
        Description: Test BMS LCM scenario for multi homing - BMS node with two interface.interface1 in qfx1 and interface2 in qfx2
        Test Steps:
           1. Delete all existing BMS nodes and create only one ironic node - the host which has two interface- interface1 in qfx1 and interace2 in qfx2
           2. Update SG to allow ping/traffic between BMS VM and regular VM
           3. Reconfigure TFTP Block size and ip link MTU
           4. Bringup one BMS LCM instance and one VM.Verify ping between VM and BMS VM instance works.
        Maintainer: vageesant@juniper.net
        '''
        self.bms_delete_nodes()
        self.bms_node_add_delete(bms_type="multi_homing")
        time.sleep(60)
        self.bms_vm_add_delete(bms_count=1)

    @preposttest_wrapper
    def test_bms_lag(self):
        '''
        Description: Test BMS LCM scenario for LAG - Link Aggregation - BMS node with two interface.interface1 and interface2 both in the same qfx
        Test Steps:
           1. Delete all existing BMS nodes and create only one ironic node - the host which has two interface- interface1 interface2 both in the same qfx.
           2. Update SG to allow ping/traffic between BMS VM and regular VM
           3. Reconfigure TFTP Block size and ip link MTU
           4. Bringup one BMS LCM instance and one VM.Verify ping between VM and BMS VM instance works.
        Maintainer: vageesant@juniper.net
        '''
        self.bms_delete_nodes()
        self.bms_node_add_delete(bms_type="link_aggregation")
        time.sleep(60)
        self.bms_vm_add_delete(bms_count=1)

    @preposttest_wrapper
    def test_bms_all(self):
        '''
        Description: SuperSet testcase for Single Interface BMS,LAG Scenario and Multi-homing scenario
        Test Steps:
           1. Delete all existing BMS nodes and create 3 ironic nodes - one single interface,one multi-homing,one lag
           2. Update SG to allow ping/traffic between BMS VM and regular VM
           3. Reconfigure TFTP Block size and ip link MTU
           4. Bringup one BMS LCM instance and one VM.Verify ping between VM and BMS VM instance works.
        Maintainer: vageesant@juniper.net
        '''
        self.bms_delete_nodes()
        self.bms_node_add_delete("all")
        time.sleep(60)
        self.bms_vm_add_delete(bms_count=3)

    def bms_vm_add_delete(self,bms_count=1):
        '''
        Not run as separate test.
        Will be called by test_bms_single_interface or  test_bms_multi_homing or test_bms_lag
        Test Step:
            1. Create tenant VN
            2. Create N BMS instance.
            3. Create regular VM and verify ping from VM to BMS VM instance works.

        Maintainer : vageesant@juniper.net
        '''
        bms_lcm_config = self.inputs.bms_lcm_config
        bms_nodes = self.inputs.bms_data
        bms_image = bms_lcm_config['bms_image']

        ironic_computes = self.connections.nova_h.get_ironic_compute_service_list()
        bms_availability_zone = "nova-baremetal"
        bms_availability_host = ironic_computes[0].host

        vn_fixture = self.create_vn()
        vn_obj = vn_fixture.obj

        vm_fixture = self.create_vm(vn_fixture=vn_fixture,
                                    image_name="ubuntu-traffic")
        bms_fixtures_list = []
        for i in xrange(bms_count):
            bms_fixtures_list.append(self.create_vm(vn_fixture=vn_fixture,
                image_name=bms_image,
                zone=bms_availability_zone,
                node_name=bms_availability_host,
                instance_type="baremetal"))

        assert vm_fixture.wait_till_vm_is_up()
        self.sleep(180)
        for bms_fixture in bms_fixtures_list:
            assert bms_fixture.verify_on_setup()

        for bms_fixture in bms_fixtures_list:
            for i in xrange(5):
               ping_result = vm_fixture.ping_with_certainty(bms_fixture.vm_ip)
               if ping_result:
                  break
            if ping_result:
                self.logger.debug("Ping to BMS Node %s is successful"%bms_fixture.vm_name)
            else:
                assert False, 'Unable to reach bms node %s'%bms_fixture.vm_name
        assert ping_result
        return True