import os
import fixtures
import testtools
import unittest
import traffic_tests
import time
#from connections import ContrailConnections
#from contrail_test_init import ContrailTestInit
from vn_test import *
from floating_ip import *
from quantum_test import *
from vnc_api_test import *
from nova_test import *
from vm_test import *
from tcutils.wrappers import preposttest_wrapper
from tcutils.commands import ssh, execute_cmd, execute_cmd_out
from servicechain.firewall.verify import VerifySvcFirewall
from ecmp.ecmp_traffic import ECMPTraffic
from ecmp.ecmp_verify import ECMPVerify
from traffic.core.stream import Stream
from traffic.core.profile import create, ContinuousProfile
from traffic.core.helpers import Host
from traffic.core.helpers import Sender, Receiver
from fabric.state import connections as fab_connections
from ecmp.ecmp_test_resource import ECMPSolnSetup
from base import BaseECMPTest                                                                                                                                                                                  
from common import isolated_creds                                                                                                                                                                              
import inspect

class TestECMPSanity(BaseECMPTest, VerifySvcFirewall, ECMPSolnSetup, ECMPTraffic, ECMPVerify):

    @classmethod
    def setUpClass(cls):
        super(TestECMPSanity, cls).setUpClass()

    def runTest(self):
        pass                                                                                                                                                                                                   
    #end runTest

    #@preposttest_wrapper
    def test_ecmp_svc_transparent_with_3_instance(self):
        """
           Description: Validate ECMP with service chaining transparent mode datapath having service instance
           Test steps:
                1.Creating vm's - vm1 and vm2 in networks vn1 and vn2.
                2.Creating a service instance in transparent mode with 3 instances.
                3.Creating a service chain by applying the service instance as a service in a policy between the VNs.
                4.Checking for ping and bidirectional tcp traffic between vm1 and vm2.
           Pass criteria: Ping between the VMs should be successful and TCP traffic should reach vm2 from vm1 and vice-versa.
           Maintainer : ganeshahv@juniper.net
        """
        self.verify_svc_transparent_datapath(
            si_count=1, svc_scaling=True, max_inst=3)
        self.logger.info('Verify Traffic Flow in both the directions')
        dst_vm_list1= [self.vm2_fixture]
        dst_vm_list2= [self.vm1_fixture]
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list1)
        self.verify_traffic_flow(self.vm2_fixture, dst_vm_list2)
        return True
    # end test_ecmp_svc_transparent_with_3_instance

    #@preposttest_wrapper
    def test_ecmp_svc_in_network_with_3_instance(self):
        """Validate ECMP with service chaining in-network mode datapath having
        service instance"""
        self.verify_svc_in_network_datapath(
            si_count=1, svc_scaling=True, max_inst=3)
        svm_ids = self.si_fixtures[0].svm_ids
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        dst_vm_list= [self.vm2_fixture]
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)
        return True
    # end test_ecmp_svc_in_network_with_3_instance

#    @preposttest_wrapper
    def test_ecmp_svc_in_network_with_static_route_no_policy(self):
        """
        Description:    Validate service chaining in-network mode datapath having a static route entries of the either virtual networks pointing to the corresponding interfaces of the
        service instance. We will not configure any policy.
        Test steps:
            1.  Creating vm's - vm1 and vm2 in networks vn1 and vn2.
            2.  Creating a service instance in in-network mode with 1 instance and left-interface of the service instance sharing the IP and both the left and the right interfaces enabled for static route.
            3.  Delete the policy.
            4.  Checking for ping and tcp traffic between vm1 and vm2.
        Pass criteria: Ping between the VMs should be successful and TCP traffic should reach vm2 from vm1.

        Maintainer : ganeshahv@juniper.net
        """
        vn1_subnet_list= ['100.1.1.0/24']
        vn2_subnet_list= ['200.1.1.0/24'] 
        self.verify_svc_in_network_datapath(si_count=1, svc_scaling=True, max_inst=1, static_route=[
                                            'None', vn2_subnet_list[0], vn1_subnet_list[0]], vn1_subnets= 
                                            vn1_subnet_list, vn2_subnets= vn2_subnet_list)
        svm_ids = self.si_fixtures[0].svm_ids
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        dst_vm_list= [self.vm2_fixture]
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)

        self.logger.info(
            '***** Will Detach the policy from the networks and delete it *****')
        self.detach_policy(self.vn1_policy_fix)
        self.detach_policy(self.vn2_policy_fix)
        self.unconfig_policy(self.policy_fixture)
        sleep(30)
        self.logger.info(
            '***** Ping and traffic between the networks should go thru fine because of the static route configuration *****')
        assert self.vm1_fixture.ping_with_certainty(self.vm2_fixture.vm_ip)

        return True
        # end test_ecmp_svc_in_network_with_static_route_no_policy

class TestECMPFeature(BaseECMPTest, VerifySvcFirewall, ECMPSolnSetup, ECMPTraffic, ECMPVerify):

    @classmethod
    def setUpClass(cls):
        super(TestECMPFeature, cls).setUpClass()

    def runTest(self):
        pass    
    #end runTest

#    @preposttest_wrapper
    def test_ecmp_svc_in_network_nat_with_3_instance(self):
        """
         Description: Validate ECMP with service chaining in-network-nat mode datapath having service instance
         Test steps:
           1.	Creating vm's - vm1 and vm2 in networks vn1 and vn2.
           2.	Creating a service instance in in-network-nat mode with 3 instances and
                left-interface of the service instances sharing the IP and enabled for static route.

           3.	Creating a service chain by applying the service instance as a service in a policy between the VNs.
           4.	Checking for ping and tcp traffic between vm1 and vm2.
         Pass criteria: Ping between the VMs should be successful and TCP traffic should reach vm2 from vm1.
         Maintainer : ganeshahv@juniper.net
        """
        self.verify_svc_in_network_datapath(
            si_count=1, svc_scaling=True, max_inst=3, svc_mode='in-network-nat')
        svm_ids = self.si_fixtures[0].svm_ids
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        dst_vm_list= [self.vm2_fixture]
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)
        return True
    # end test_ecmp_svc_in_network_nat_with_3_instance

#    @preposttest_wrapper
    def test_ecmp_svc_in_network_with_3_instance_add_flows(self):
        """Validate ECMP with service chaining in-network mode datapath having
        service instance. Add flows on top and verify that the current flows are unaffected"""
        self.verify_svc_in_network_datapath(
            si_count=1, svc_scaling=True, max_inst=3)
        svm_ids = self.si_fixtures[0].svm_ids
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        vm_list = [self.vm1_fixture, self.vm2_fixture]
        for vm in vm_list:
            vm.install_pkg("Traffic")
        old_stream1 = Stream(
            protocol="ip", proto="icmp", src=self.vm1_fixture.vm_ip,
            dst=self.vm2_fixture.vm_ip, sport=unicode(10000), dport=unicode(11000))
        old_stream2 = Stream(
            protocol="ip", proto="udp", src=self.vm1_fixture.vm_ip,
            dst=self.vm2_fixture.vm_ip, sport=unicode(10000), dport=unicode(11000))
        old_stream3 = Stream(
            protocol="ip", proto="tcp", src=self.vm1_fixture.vm_ip,
            dst=self.vm2_fixture.vm_ip, sport=unicode(10000), dport=unicode(11000))
        self.old_stream_list = [old_stream1, old_stream2, old_stream3]
        
        dst_vm_list= [self.vm2_fixture]
        self.old_sender, self.old_receiver= self.start_traffic(self.vm1_fixture, dst_vm_list, self.old_stream_list, self.vm1_fixture.vm_ip, self.vm2_fixture.vm_ip)
        self.logger.info(
            'Sending traffic for 10 seconds and will start more flows')
        time.sleep(10)
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)
        self.verify_flow_records(self.vm1_fixture, self.vm1_fixture.vm_ip, self.vm2_fixture.vm_ip)
        self.stop_traffic(self.old_sender, self.old_receiver, dst_vm_list, self.old_stream_list)
        return True
    # end test_ecmp_svc_in_network_with_3_instance_add_flows

#    @preposttest_wrapper
    def test_ecmp_svc_in_network_with_3_instance_diff_proto(self):
        """Validate ECMP with service chaining in-network mode datapath having
        service instance. Send 3 different protocol traffic to the same destination"""
        self.verify_svc_in_network_datapath(
            si_count=1, svc_scaling=True, max_inst=3)
        svm_ids = self.si_fixtures[0].svm_ids
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        vm_list = [self.vm1_fixture, self.vm2_fixture]
        for vm in vm_list:
            vm.install_pkg("Traffic")

        stream1 = Stream(
            protocol="ip", proto="icmp", src=self.vm1_fixture.vm_ip,
            dst=self.vm2_fixture.vm_ip, sport=unicode(8000), dport=unicode(9000))
        stream2 = Stream(
            protocol="ip", proto="udp", src=self.vm1_fixture.vm_ip,
            dst=self.vm2_fixture.vm_ip, sport=unicode(8000), dport=unicode(9000))
        stream3 = Stream(
            protocol="ip", proto="tcp", src=self.vm1_fixture.vm_ip,
            dst=self.vm2_fixture.vm_ip, sport=unicode(8000), dport=unicode(9000))
        self.stream_list = [stream1, stream2, stream3]
        
        dst_vm_list= [self.vm2_fixture]
        self.sender, self.receiver= self.start_traffic(self.vm1_fixture, dst_vm_list, self.stream_list, self.vm1_fixture.vm_ip, self.vm2_fixture.vm_ip)

        self.logger.info('Sending traffic for 10 seconds')
        time.sleep(10)
        
        self.verify_flow_records(self.vm1_fixture, self.vm1_fixture.vm_ip, self.vm2_fixture.vm_ip)
        
        self.stop_traffic(self.sender, self.receiver, dst_vm_list, self.stream_list)
        return True
    # end test_ecmp_svc_in_network_with_3_instance_diff_proto

#    @preposttest_wrapper
    def test_ecmp_svc_in_network_with_3_instance_incr_dip(self):
        """Validate ECMP with service chaining in-network mode datapath having
        service instance. Send traffic to 3 different DIPs"""
        self.verify_svc_in_network_datapath(
            si_count=1, svc_scaling=True, max_inst=3)
        svm_ids = self.si_fixtures[0].svm_ids
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        dest_vm2 = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=self.vn2_fixture.obj, flavor='contrail_flavor_small', image_name='ubuntu-traffic', vm_name='dest_vm2'))
        assert dest_vm2.verify_on_setup()
        dest_vm3 = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=self.vn2_fixture.obj, flavor='contrail_flavor_small', image_name='ubuntu-traffic', vm_name='dest_vm3'))
        assert dest_vm3.verify_on_setup()
        vm_list = [self.vm1_fixture, self.vm2_fixture, dest_vm2, dest_vm3]
        for vm in vm_list:
            vm.install_pkg("Traffic")

        stream1 = Stream(
            protocol="ip", proto="tcp", src=self.vm1_fixture.vm_ip,
            dst=self.vm2_fixture.vm_ip, sport=unicode(8000), dport=unicode(9000))
        stream2 = Stream(
            protocol="ip", proto="tcp", src=self.vm1_fixture.vm_ip,
            dst=dest_vm2.vm_ip, sport=unicode(8000), dport=unicode(9000))
        stream3 = Stream(
            protocol="ip", proto="tcp", src=self.vm1_fixture.vm_ip,
            dst=dest_vm3.vm_ip, sport=unicode(8000), dport=unicode(9000))

        self.stream_list = [stream1, stream2, stream3]
        
        dst_vm_list= [self.vm2_fixture]
        self.sender, self.receiver= self.start_traffic(self.vm1_fixture, dst_vm_list, self.stream_list, 
                self.vm1_fixture.vm_ip, self.vm2_fixture.vm_ip)
        self.logger.info('Sending traffic for 10 seconds')
        time.sleep(10)
        self.verify_flow_records(self.vm1_fixture, self.vm1_fixture.vm_ip, self.vm2_fixture.vm_ip)
        self.stop_traffic(self.sender, self.receiver, dst_vm_list, self.stream_list)
        return True
    # end test_ecmp_svc_in_network_with_3_instance_incr_dip


#    @preposttest_wrapper
    def test_ecmp_svc_in_network_with_policy_bind_unbind(self):
        """Validate ECMP with service chaining in-network mode datapath having
        multiple service chain. Unbind and bind back the policy and check traffic."""
        self.verify_svc_in_network_datapath(
            si_count=1, svc_scaling=True, max_inst=3)
        svm_ids = self.si_fixtures[0].svm_ids
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        dst_vm_list= [self.vm2_fixture]
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)

        self.logger.info(
            'Will Detach the policy from the networks and delete it')
        self.detach_policy(self.vn1_policy_fix)
        self.detach_policy(self.vn2_policy_fix)
        self.unconfig_policy(self.policy_fixture)
        sleep(30)
        self.logger.info('Traffic between the VMs should fail now')
        # Ping from left VM to right VM; expected to fail
        errmsg = "Ping to right VM ip %s from left VM passed; expected to fail" % self.vm2_fixture.vm_ip
        assert self.vm1_fixture.ping_with_certainty(
            self.vm2_fixture.vm_ip, expectation=False), errmsg

        self.logger.info(
            'Will Re-Configure the policy and attach it to the networks')
        self.policy_fixture = self.config_policy(self.policy_name, self.rules)
        self.vn1_policy_fix = self.attach_policy_to_vn(
            self.policy_fixture, self.vn1_fixture)
        self.vn2_policy_fix = self.attach_policy_to_vn(
            self.policy_fixture, self.vn2_fixture)
        sleep(30)
        self.logger.info('Traffic between the VMs should pass now')
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)
        return True
    # end test_ecmp_svc_in_network_with_policy_bind_unbind


class TestECMPScale(BaseECMPTest, VerifySvcFirewall, ECMPSolnSetup, ECMPTraffic, ECMPVerify):
    
    @classmethod
    def setUpClass(cls):
        super(TestECMPScale, cls).setUpClass()

    def runTest(self):
        pass    
    #end runTest

#    @preposttest_wrapper
    def test_ecmp_svc_in_network_nat_scale_max_instances(self):
        """
         Description: Validate ECMP with service chaining in-network-nat mode datapath by incrementing the max instances
                    from 4 in steps of 4 till 16
         Test steps:
           1.	Creating vm's - vm1 and vm2 in networks vn1 and vn2.
           2.	Creating a service instance in in-network-nat mode with 4 instances and
                left-interface of the service instances sharing the IP.
           3.	Creating a service chain by applying the service instance as a service in a policy between the VNs.
           4.	Checking for ping and tcp traffic between vm1 and vm2.
           5.   Delete the Service Instances and Service Template.
           6.   Increment the service instance max count by 4 and repeat steps 1-5.
           7.   This testcase will be run in only multiple compute node scenario.
         Pass criteria: Ping between the VMs should be successful and TCP traffic should reach vm2 from vm1.
         Maintainer : ganeshahv@juniper.net
        """
        if len(self.inputs.compute_ips) > 1:
            for i in range(4, 17, 4):
                self.logger.info(
                    '***** Will launch %s instances in the Service Chain *****' % i)
                self.verify_svc_in_network_datapath(
                    si_count=1, svc_scaling=True, max_inst=i, svc_mode='in-network-nat')
                svm_ids = self.si_fixtures[0].svm_ids
                self.get_rt_info_tap_intf_list(
                    self.vn1_fixture, self.vm1_fixture, svm_ids)
                dst_vm_list= [self.vm2_fixture]
                self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)
                for si in self.si_fixtures:
                    self.logger.info('Deleting the SI %s' % si.st_name)
                    si.cleanUp()
                    si.verify_on_cleanup()
                    self.remove_from_cleanups(si)
                self.logger.info('Deleting the ST %s' %
                                 self.st_fixture.st_name)
                self.st_fixture.cleanUp()
                self.remove_from_cleanups(self.st_fixture)
        else:
            self.logger.info(
                'Scaling test. Will run only on multiple node setup')
        return True
    # end test_ecmp_svc_in_network_nat_scale_max_instances

#    @preposttest_wrapper
    def test_ecmp_svc_in_network_with_multiple_service_chains(self):
        """Validate ECMP with service chaining in-network mode datapath having
        multiple service chains in parallel between the same two networks"""
        vn_obj_list = []
        vm_list = []
        for i in range(1, 6):
            vn1_subnets = '10.%s.1.0/24' % i
            vn1_subnet_list= [vn1_subnets]
            vn2_subnets = '20.%s.1.0/24' % i
            vn2_subnet_list= [vn2_subnets]
            self.verify_svc_in_network_datapath(si_count=1, svc_scaling=True, max_inst=3, vn1_subnets= vn1_subnet_list, vn2_subnets= vn2_subnet_list)
            dst_vm_list= [self.vm2_fixture]
            self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)
        return True
    # end test_ecmp_svc_in_network_with_multiple_service_chains

#    @preposttest_wrapper
    def test_ecmp_svc_in_network_with_3_instance_service_restarts(self):
        """Validate ECMP after restarting control and vrouter services with service chaining in-network mode datapath having
        service instance"""
        self.verify_svc_in_network_datapath(
            si_count=1, svc_scaling=True, max_inst=3)
        svm_ids = self.si_fixtures[0].svm_ids
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        dst_vm_list= [self.vm2_fixture]
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)

        for compute_ip in self.inputs.compute_ips:
            self.inputs.restart_service('contrail-vrouter', [compute_ip])
        self.logger.info('Sleeping for 30 seconds')
        sleep(30)
        
        self.vm1_fixture.verify_vm_in_agent()
        self.vm1_fixture.wait_till_vm_is_up()
        self.vm2_fixture.verify_vm_in_agent()
        self.vm2_fixture.wait_till_vm_is_up()

        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        fab_connections.clear()
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)

        for bgp_ip in self.inputs.bgp_ips:
            self.inputs.restart_service('contrail-control', [bgp_ip])
        self.logger.info('Sleeping for 30 seconds')
        sleep(30)

        self.vm1_fixture.verify_vm_in_agent()
        self.vm1_fixture.wait_till_vm_is_up()
        self.vm2_fixture.verify_vm_in_agent()
        self.vm2_fixture.wait_till_vm_is_up()

        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        fab_connections.clear()
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)
        return True
    # end test_ecmp_svc_in_network_with_3_instance_service_restarts

#    @preposttest_wrapper
    def test_ecmp_svc_in_network_with_3_instance_reboot_nodes(self):
        """Validate ECMP after restarting control and vrouter services with service chaining in-network mode datapath having
        service instance. Check the ECMP behaviour after rebooting the nodes"""
        cmd = 'reboot'
        self.verify_svc_in_network_datapath(
            si_count=1, svc_scaling=True, max_inst=3, flavor='m1.medium')
        svm_ids = self.si_fixtures[0].svm_ids
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        
        dst_vm_list= [self.vm2_fixture]
        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)

        self.logger.info('Will reboot the Compute and Control nodes')
        nodes= []
        nodes= list(set(self.inputs.compute_ips + self.inputs.bgp_ips))
        for node in nodes:
            if node != self.inputs.cfgm_ips[0]:
                self.logger.info('Will reboot the node %s' %
                                 socket.gethostbyaddr(node)[0])
                self.inputs.run_cmd_on_server(
                    node, cmd, username='root', password='c0ntrail123')
            else:
                self.logger.info(
                    'Node %s is the first cfgm. Will skip rebooting it.' %
                    socket.gethostbyaddr(node)[0])
        self.logger.info('Sleeping for 240 seconds')
        sleep(240)
        self.logger.info(
            'Will check the state of the SIs and power it ON, if it is in SHUTOFF state')
        for vm in self.nova_fixture.get_vm_list():
            if vm.status != 'ACTIVE':
                self.logger.info('Will Power-On %s' % vm.name)
                vm.start()
        self.logger.info('Sleeping for 30 seconds')
        sleep(30)
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)
        fab_connections.clear()
        self.vm1_fixture.verify_vm_in_agent()
        self.vm1_fixture.wait_till_vm_is_up()
        self.vm2_fixture.verify_vm_in_agent()
        self.vm2_fixture.wait_till_vm_is_up()

        self.verify_traffic_flow(self.vm1_fixture, dst_vm_list)
        return True
    # end test_ecmp_svc_in_network_with_3_instance_reboot_nodes

    def remove_from_cleanups(self, fix):
        for cleanup in self._cleanups:
            if fix.cleanUp in cleanup:
                self._cleanups.remove(cleanup)
                break

class TestECMPwithFIP(BaseECMPTest, VerifySvcFirewall, ECMPSolnSetup, ECMPTraffic, ECMPVerify):

    @classmethod
    def setUpClass(cls):
        super(TestECMPwithFIP, cls).setUpClass()

    def runTest(self):
        pass    
    #end runTest
    
#    @preposttest_wrapper
    def test_ecmp_with_svc_with_fip_dest(self):
        """Validate ECMP with service chaining and FIP at the destination"""
        self.verify_svc_in_network_datapath(
            si_count=1, svc_scaling=True, max_inst=3)
        self.logger.info('.' * 80)
        self.logger.info(
            'We will create 3 VMs at the destination and make them share the same FIP address')
        self.logger.info('.' * 80)
        self.my_fip_name = 'fip'
        self.my_fip = '10.1.1.10'

        #self.fvn= self.useFixture( VNFixture(project_name= self.inputs.project_name, connections= self.connections,vn_name='fvn', inputs= self.inputs, subnets=['30.1.1.0/29']))
        self.vm2_1 = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=self.vn2_fixture.obj, flavor='contrail_flavor_small', image_name='ubuntu-traffic', vm_name='vm2_1'))
        self.vm2_2 = self.useFixture(
            VMFixture(
                project_name=self.inputs.project_name, connections=self.connections,
                vn_obj=self.vn2_fixture.obj, flavor='contrail_flavor_small', image_name='ubuntu-traffic', vm_name='vm2_2'))

        #assert self.fvn.verify_on_setup()
        assert self.vm2_1.verify_on_setup()
        assert self.vm2_2.verify_on_setup()

        self.fip_fixture = self.useFixture(
            FloatingIPFixture(
                project_name=self.inputs.project_name, inputs=self.inputs,
                connections=self.connections, pool_name='some-pool1', vn_id=self.vn1_fixture.vn_id))
        assert self.fip_fixture.verify_on_setup()

        self.fvn_obj = self.vnc_lib.virtual_network_read(
            id=self.vn1_fixture.vn_id)
        self.fip_pool_obj = FloatingIpPool('some-pool1', self.fvn_obj)
        self.fip_obj = FloatingIp('fip', self.fip_pool_obj, '10.1.1.10', True)

        # Get the project_fixture
        self.project_fixture = self.useFixture(ProjectFixture(
            vnc_lib_h=self.vnc_lib, project_name=self.inputs.project_name, connections=self.connections))
        # Read the project obj and set to the floating ip object.
        self.fip_obj.set_project(self.project_fixture.project_obj)

        self.vn2_fq_name = self.vn2_fixture.vn_fq_name
        self.vn2_vrf_name = self.vn2_fixture.vrf_name
        self.vn2_ri_name = self.vn2_fixture.ri_name
        self.vmi1_id = self.vm2_fixture.tap_intf[
            self.vn2_fixture.vn_fq_name]['uuid']
        self.vmi2_id = self.vm2_1.tap_intf[
            self.vn2_fixture.vn_fq_name]['uuid']
        self.vmi3_id = self.vm2_2.tap_intf[
            self.vn2_fixture.vn_fq_name]['uuid']
        self.vm2_intf = self.vnc_lib.virtual_machine_interface_read(
            id=self.vmi1_id)
        self.vm2_1_intf = self.vnc_lib.virtual_machine_interface_read(
            id=self.vmi2_id)
        self.vm2_2_intf = self.vnc_lib.virtual_machine_interface_read(
            id=self.vmi3_id)
        for intf in [self.vm2_intf, self.vm2_1_intf, self.vm2_2_intf]:
            self.fip_obj.add_virtual_machine_interface(intf)
        self.vnc_lib.floating_ip_create(self.fip_obj)
        self.addCleanup(self.vnc_lib.floating_ip_delete, self.fip_obj.fq_name)
        svm_ids = self.si_fixtures[0].svm_ids
        self.get_rt_info_tap_intf_list(
            self.vn1_fixture, self.vm1_fixture, svm_ids)

        recv_vm_list = []
        recv_vm_list = [self.vm2_fixture, self.vm2_1, self.vm2_2]
        for vm in recv_vm_list:
            vm.install_pkg("Traffic")
        self.vm1_fixture.install_pkg("Traffic")
        self.verify_traffic_flow(self.vm1_fixture, recv_vm_list, self.vm1_fixture.vm_ip, '10.1.1.10')
        
        return True
    # end test_ecmp_with_svc_with_fip_dest

#    @preposttest_wrapper
    def test_ecmp_bw_three_vms_add_del_same_fip(self):
        '''Test communication between three VMs who have borrowed the FIP from common FIP pool.Delete two of the VMs and check that traffic flow is unaffected.
        '''
        self.setup_common_objects()
        vm_list = []
        vm_list = [self.vm1, self.vm2, self.vm3]
        
        self.logger.info('Will send traffic from the fvn_vm1 to 30.1.1.3')
        self.stream_list= self.setup_streams(self.fvn_vm1, vm_list, self.fvn_vm1.vm_ip, self.my_fip)
        self.sender, self.receiver= self.start_traffic(self.fvn_vm1, vm_list, self.stream_list, self.fvn_vm1.vm_ip, self.my_fip)
      
        self.logger.info(
            'Will disassociate the fip address from two VMs and check that there should be no traffic loss.')
        self.fip_obj.del_virtual_machine_interface(self.vm1_intf)
        self.fip_obj.del_virtual_machine_interface(self.vm3_intf)
        self.vnc_lib.floating_ip_update(self.fip_obj)
        sleep(5) 
        self.logger.info(
                      'Will re-associate the fip address to the VMs ')
        self.fip_obj.add_virtual_machine_interface(self.vm3_intf)
        self.fip_obj.add_virtual_machine_interface(self.vm1_intf)
        self.vnc_lib.floating_ip_update(self.fip_obj)

        self.verify_flow_records(self.fvn_vm1, self.fvn_vm1.vm_ip, self.my_fip)
        self.stop_traffic(self.sender, self.receiver, vm_list, self.stream_list)

        return True
    # end test_ecmp_bw_three_vms_add_del_same_fip

#    @preposttest_wrapper
    def test_ecmp_bw_three_vms_same_fip_incr_sport(self):
        '''Test communication between three VMs who have borrowed the FIP from common FIP pool. Increment sport and have 3 flows setup.
        '''
        self.setup_common_objects()
        vm_list = [self.vm1, self.vm2, self.vm3]
        stream1 = Stream(protocol="ip", proto="udp", src=self.fvn_vm1.vm_ip,
                         dst=self.my_fip, sport=unicode(10000), dport=self.dport1)
        stream2 = Stream(protocol="ip", proto="udp", src=self.fvn_vm1.vm_ip,
                         dst=self.my_fip, sport=unicode(11000), dport=self.dport1)
        stream3 = Stream(protocol="ip", proto="udp", src=self.fvn_vm1.vm_ip,
                         dst=self.my_fip, sport=unicode(12000), dport=self.dport1)
        stream_list = [stream1, stream2, stream3]
        
        self.sender, self.receiver= self.start_traffic(self.fvn_vm1, vm_list, stream_list, self.fvn_vm1.vm_ip, self.my_fip)
        self.logger.info('Sending traffic for 10 seconds')
        time.sleep(10)
        self.verify_flow_records(self.fvn_vm1, self.fvn_vm1.vm_ip, self.my_fip)
        return True

    # end test_ecmp_bw_three_vms_same_fip_incr_sport

#    @preposttest_wrapper
    def test_ecmp_bw_three_vms_same_fip_incr_sip(self):
        '''Test communication between three VMs who have borrowed the FIP from common FIP pool. Increment SIP and have 3 flows setup.
        '''
        self.setup_common_objects()
        vm_list = [self.vm1, self.vm2, self.vm3]
        stream1 = Stream(protocol="ip", proto="udp", src=self.fvn_vm1.vm_ip,
                         dst=self.my_fip, sport=self.udp_src, dport=self.dport1)
        stream2 = Stream(protocol="ip", proto="udp", src=self.fvn_vm2.vm_ip,
                         dst=self.my_fip, sport=self.udp_src, dport=self.dport1)
        stream3 = Stream(protocol="ip", proto="udp", src=self.fvn_vm3.vm_ip,
                         dst=self.my_fip, sport=self.udp_src, dport=self.dport1)
        stream_list = [stream1, stream2, stream3]

        self.sender, self.receiver= self.start_traffic(self.fvn_vm1, vm_list, stream_list, self.fvn_vm1.vm_ip, self.my_fip)
        self.logger.info('Sending traffic for 10 seconds')
        time.sleep(10)
        self.verify_flow_records(self.fvn_vm1, self.fvn_vm1.vm_ip, self.my_fip)
        return True

#
#    def setUp(self):
#        super(ECMPSanity, self).setUp()
#        if 'PARAMS_FILE' in os.environ:
#            self.ini_file = os.environ.get('PARAMS_FILE')
#        else:
#            self.ini_file = 'params.ini'
#        self.inputs = self.useFixture(ContrailTestInit(self.ini_file))
#        self.connections = ContrailConnections(self.inputs)
#        self.quantum_fixture = self.connections.quantum_fixture
#        self.nova_fixture = self.connections.nova_fixture
#        self.vnc_lib = self.connections.vnc_lib
#        self.logger = self.inputs.logger
#        self.analytics_obj = self.connections.analytics_obj
#        self.api_s_inspect = self.connections.api_server_inspect
#        self.cn_inspect = self.connections.cn_inspect
#        self.agent_inspect = self.connections.agent_inspect
#        self.quantum_fixture = self.connections.quantum_fixture
#
#    def cleanUp(self):
#        self.logger.info("Cleaning up")
#        super(ECMPSanity, self).cleanUp()


