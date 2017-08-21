import os
import base64
import struct
import socket
from netaddr import IPAddress, IPNetwork
from synchronizers.swarm.swarmsyncstep import SwarmSyncStep
from synchronizers.new_base.syncstep import *
from xos.logger import observer_logger as logger
from synchronizers.new_base.ansible_helper import *
from synchronizers.new_base.modelaccessor import *

import synchronizers.swarm.swarmlog as slog 

class SyncControllerNetworks(SwarmSyncStep):
    requested_interval = 0
    provides=[Network]
    observes=ControllerNetwork
    playbook='sync_controller_networks.yaml'

    def alloc_subnet(self, uuid):
        # 16 bits only
        slog.debug("uuid: %s" % str(uuid))

        uuid_masked = uuid & 0xffff
        a = 10
        b = uuid_masked >> 8
        c = uuid_masked & 0xff
        d = 0

        cidr = '%d.%d.%d.%d/24'%(a,b,c,d)
        slog.debug("cidr: %s" % str(cidr))

        return cidr

    def alloc_gateway(self, subnet):
        # given a CIDR, allocate a default gateway using the .1 address within the subnet.
        #    10.123.0.0/24 --> 10.123.0.1
        #    207.141.192.128/28 --> 207.141.192.129
        (network, bits) = subnet.split("/")
        network=network.strip()
        bits=int(bits.strip())
        netmask = (~(pow(2,32-bits)-1) & 0xFFFFFFFF)
        ip = struct.unpack("!L", socket.inet_aton(network))[0]
        ip = ip & netmask | 1
        slog.info("subnet: %s    gateway: %s" % (subnet,ip)) 
        return socket.inet_ntoa(struct.pack("!L", ip))

    def chk_net_exist(self, controller_network, swarm_manager_address):
        duplicated_flag = False
        try: 
            slog.debug("network_name to check: %s" % controller_network.network.name)

            import docker 
            docker_api_base_url = "tcp://%s:4243" % swarm_manager_address
            slog.info("Docker API Base URL: %s" % docker_api_base_url) 
            my_client = docker.DockerClient(base_url=docker_api_base_url)
            net = my_client.networks.get(controller_network.network.name)
            slog.debug("network.id                  : %s" % net.id)
            slog.debug("network.name                : %s" % net.name)
            slog.debug("network.attrs[IPAM][Config] : %s" % net.attrs['IPAM']['Config'])
            slog.debug("network.attrs               : %s" % net.attrs)
        except Exception as ex:
            slog.info("Exception: %s" % str(ex.args))
            slog.info("Exception: %s" % str(ex))
            duplicated_flag = False  # There is no same network.
        else:
            duplicated_flag = True   # There is same network.
        slog.debug("network duplicated_flag: %s" % duplicated_flag)
        return duplicated_flag 

    def save_controller_network(self, controller_network):
        network_name = controller_network.network.name 
        #subnet_name = '%s-%d'%(network_name, controller_network.pk)
        #slog.info("network_name: %s    subnet_name: %s" % (network_name, subnet_name))
        if controller_network.subnet and controller_network.subnet.strip():
            # If a subnet is already specified (pass in by the creator), then
            # use that rather than auto-generating one.
            cidr = controller_network.subnet.strip()
            slog.info("subnet CIDR_MS : %s" % cidr) 
        else:
            cidr = self.alloc_subnet(controller_network.pk)
            slog.info("subnet CIDR_AMS: %s" % cidr) 

        if controller_network.network.start_ip and controller_network.network.start_ip.strip():
            start_ip = controller_network.network.start_ip.strip()
            # FIXME: this assignment(gateway=start_ip) is temporary code.
            #        I would add a attribute gateway on core_network model.
            controller_network.gateway = start_ip  
        else:
            start_ip = None
            controller_network.gateway = self.alloc_gateway(cidr)

        if controller_network.network.end_ip and controller_network.network.end_ip.strip():
            end_ip = controller_network.network.end_ip.strip()
        else:
            end_ip = None
        slog.info("Start IP Address: %s    End IP Address: %s" % (start_ip, end_ip)) 

        self.cidr=cidr
        slice = controller_network.network.owner


        opt_driver = "--driver=overlay" # default driver for swarm
        opt_ipam_driver = " "
        opt_ipam_neutron_opt = " "
        if controller_network.network.template.shared_network_name is not None:
            if len(controller_network.network.template.shared_network_name) > 1:
            if controller_network.network.template.shared_network_name.__contains__("kuryr"):
                opt_driver = "--driver=%s" % controller_network.network.template.shared_network_name
                opt_ipam_driver = "--ipam-driver=%s" % controller_network.network.template.shared_network_name
                opt_ipam_neutron_opt = "--ipam-opt=neutron.pool.uuid=%s  -o neutron.pool.uuid=%s  -o neutron.net.uuid=%s" % (
                                        controller_network.network.labels,
                                        controller_network.network.labels,
                                        controller_network.network.name)


        swarm_manager_url = controller_network.controller.auth_url
        (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
        slog.info("swarm_manager_address: %s    docker_registry_port: %s" % 
                 (swarm_manager_address, docker_registry_port))

        # check if this controller network is created already on swarm cluster.
        duplicated_flag = self.chk_net_exist(controller_network, swarm_manager_address)

        network_fields = {
                            'swarm_manager_address' : swarm_manager_address,
                            'network_name': network_name,
                            #'subnet_name': subnet_name,
                            'ansible_tag': '%s-%s@%s'%(
                                                    network_name,
                                                    slice.slicename,
                                                    controller_network.controller.name),
                            'opt_driver': opt_driver,
                            'opt_ipam_driver': opt_ipam_driver,
                            'opt_ipam_neutron_opt': opt_ipam_neutron_opt,
                            'opt_subnet': "--subnet=%s" % cidr,
                            'opt_gateway': "--gateway=%s" % controller_network.gateway,
                            'start_ip': start_ip,
                            'end_ip': end_ip,
                            'duplicated': duplicated_flag,
                            'delete': False
                            } 
        slog.info("network_fields: %s" % network_fields) 

        return network_fields

    def map_sync_inputs(self, controller_network):
        # make sure to not sync a shared network
        if (controller_network.network.template.shared_network_name or controller_network.network.template.shared_network_id):
            return SyncStep.SYNC_WITHOUT_RUNNING

        slog.debug("network owner: %s    creator: %s" % (
                    controller_network.network.owner, 
                    controller_network.network.owner.creator
                    ))
        if controller_network.network.owner and controller_network.network.owner.creator:
            return self.save_controller_network(controller_network)
        else:
            slog.info("I could not create network controller information %s" % controller_network)
            raise Exception('I could not create network controller %s'%controller_network)

    def map_sync_outputs(self, controller_network, res):
        slog.debug("ansible playbook ressult: %s" % str(res)) 
        slog.debug("ansible playbook ressult[1][stdout]: %s" % str(res[1]['stdout'])) 
        
        res_stdout = res[1]['stdout'] 
        json_content = json.loads(res_stdout)
        slog.debug("json_content: %s" % str(json_content)) 
        network_id = json_content[0]['Id']
        slog.debug("network_id: %s" % str(network_id))
        subnet_id = "%s-subnet-%s" % (network_id, self.cidr)
        slog.debug("subnet_id: %s" % str(subnet_id)) 

        controller_network.net_id = network_id
        controller_network.subnet = self.cidr
        controller_network.subnet_id = subnet_id
        controller_network.backend_status = '1 - OK'

        controller_network.save()

    def map_delete_inputs(self, controller_network):
        # make sure to not delete a shared network
        if (controller_network.network.template.shared_network_name or controller_network.network.template.shared_network_id):
            return

        try:
            slice = controller_network.network.owner
        except:
            raise Exception('Could not get slice for Network %s' % controller_network.network.name)

        network_name = controller_network.network.name
        #subnet_name = '%s-%d'%(network_name,controller_network.pk)
        cidr = controller_network.subnet
        network_fields = {
                        'network_name':network_name,
                        'ansible_tag':'%s-%s@%s'%(
                                                network_name,
                                                slice.slicename,
                                                controller_network.controller.name),
                        'delete':True
                        }

        return network_fields

