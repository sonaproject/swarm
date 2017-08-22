import os
import base64
import json
import time

from xos.logger import observer_logger as logger
from synchronizers.new_base.modelaccessor import *

import synchronizers.swarm.swarmlog as slog

import docker 


def search_instance(container_name):
    instance_list = Instance.objects.all()
    for instance in instance_list:
        slog.debug("container_name: %s    service_name: %s" % (container_name, instance.name))
        if container_name.__contains__(instance.name):
            slog.debug("%s contains %s" % (container_name, instance.name))
            str_idx = container_name.find(instance.name)
            if str_idx == 0:  # If matching offset is 0.
                return instance
    slog.debug("There is no instance tuple on XOS DB")
    return None


def search_port(ip_address):
    try:
        slog.debug("container ip_address: %s" % ip_address)
        port = Port.objects.get(ip=ip_address)
        slog.debug("port object: %s" % str(port))
        if port is None:
            slog.debug("%s does not exist, I would create new port tuple" % ip_address)
            return None
        slog.debug("%s(%s) already exists, I have nothing to do" % (port.ip, port.mac))
        return port
    except Exception as ex:
        slog.error("Exception: type(%s)   %s" % (type(ex), ex.args))
        slog.error("Exception: %s" % str(ex))
        return None


def get_swarm_manager_address():
    controller = Controller.objects.get(backend_type="Swarm")
    if controller is None:
        controller = Controller.objects.first()
    swarm_manager_url = controller.auth_url
    slog.info("swarm_manager_url: %s" % swarm_manager_url)
    (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
    slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (
                swarm_manager_address, docker_registry_port)) 
    return swarm_manager_address



def transform_ip_addr(cidr): 
    try:
        ip_addr = cidr.split('/')
        slog.debug("ip_addr : %s" % ip_addr[0])
        return ip_addr[0]
    except Exception as ex:
        slog.error("Exception: type(%s)   %s" % (type(ex), ex.args))
        slog.error("Exception: %s" % str(ex))
        return None 
   

def monitor_thr(models_active):
    slog.debug("models_active: %s" % models_active)

    swarm_manager_address = get_swarm_manager_address() 
    docker_api_base_url = "tcp://%s:4243" % swarm_manager_address 
    slog.debug("docker_api_base_url: %s" % docker_api_base_url)
    my_client = docker.DockerClient(base_url=docker_api_base_url)

    while True:
        try: 
            # To extract network list from core_network model  
            network_list = Network.objects.all()
            for network in network_list:
                # To get docker network information from swarm manager
                slog.debug("network.name: %s" % network.name)
                docker_net = my_client.networks.get(network.name)
                container_list = docker_net.attrs['Containers'].values()

                # To extract ip address and container name which uses its network
                for container in container_list:
                    slog.debug("Container name: %s" % container["Name"])
                    slog.debug("IPv4          : %s" % container["IPv4Address"])
                    slog.debug("MAC           : %s" % container["MacAddress"])
                    slog.debug("EndpointID    : %s" % container["EndpointID"])

                    ip_addr = transform_ip_addr(container["IPv4Address"])
                    # Check if same port tuple is on core_port.
                    port_info = search_port(ip_addr) 
                    if port_info is not None: # port already exists, nothing to do.
                        continue 

                    # To search instance name with container["Name"]
                    instance = search_instance(container["Name"])
                    if instance is None:
                        slog.debug("%s is not container which is created by XOS" % container["Name"])
                        continue

                    # To insert port tuple on core_port model 
                    new_port = Port()
                    new_port.ip      = ip_addr
                    new_port.mac     = container["MacAddress"]
                    new_port.port_id = container["EndpointID"]
                    new_port.leaf_model_name = "Port"
                    new_port.xos_created = True
                    new_port.instance_id = instance.id
                    new_port.network_id  = network.id
                    new_port.save() 
        except Exception as ex:
            slog.error("Exception: %s   %s" % (type(ex), ex.args))
            # slog.error("Exception: %s" % str(ex))
            # TODO  check DockerClient is disconnected or expired.
            my_client = docker.DockerClient(base_url=docker_api_base_url)

        time.sleep(5)
