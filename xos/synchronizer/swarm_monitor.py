import os
import base64
import json
import time
import sys, traceback

from xos.logger import observer_logger as logger
from synchronizers.new_base.modelaccessor import *

import synchronizers.swarm.swarmlog as slog 

import docker 


def search_instance(container_name):
    try:
        instance_list = Instance.objects.all()
        for instance in instance_list:
            slog.debug("container_name: %s    service_name: %s" % (container_name, instance.instance_name))
            if container_name.__contains__(instance.instance_name):
                slog.debug("%s contains %s" % (container_name, instance.instance_name))
                str_idx = container_name.find(instance.instance_name)
                if str_idx == 0:  # If matching offset is 0.
                    slog.debug("Matched record (%s, %s)" % (container_name, instance.instance_name))
                    return instance
        slog.debug("There is no instance tuple on XOS DB")
        return None
    except Exception as ex:
        slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
        slog.error("%s" % str(traceback.format_exc()))
        return None



def search_port(network, instance):
    try:
        slog.debug("network: %s   instance: %s" % (network.name, instance.name))
        port = Port.objects.filter(network_id=network.id, instance_id=instance.id)
        slog.debug("(%s, %s)  port object count: %s" % (network.name, instance.name, len(port)))
        if len(port) == 0:
            slog.debug("(%s, %s) does not exist, I would create new port tuple" % (network.name, instance.name))
            return None
        slog.debug("(%s, %s) Port already exists (%s)" % (network.name, instance.name, port[0].ip))
        return port[0]
    except Exception as ex:
        slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
        slog.error("%s" % str(traceback.format_exc()))
        return None


def get_swarm_manager_address():
    try:
        controller = Controller.objects.get(backend_type="Swarm")
        if controller is None:
            controller = Controller.objects.first()
        swarm_manager_url = controller.auth_url
        slog.info("swarm_manager_url: %s" % swarm_manager_url)
        (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
        slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (
                    swarm_manager_address, docker_registry_port)) 
        return swarm_manager_address
    except Exception as ex:
        slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
        slog.error("%s" % str(traceback.format_exc()))
        return None 


def transform_ip_addr(cidr): 
    try:
        ip_addr = cidr.split('/')
        slog.debug("ip_addr : %s" % ip_addr[0])
        return ip_addr[0]
    except Exception as ex:
        slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
        slog.error("%s" % str(traceback.format_exc()))
        return None 


def get_worker_conn_list(my_client):
    swarm_node_conn_list = []
    try: 
        swarm_nodes = my_client.nodes.list()
        for node in swarm_nodes:
            # To extract ip address, hostname of swarm node
            try:
                hostname = node.attrs["Description"]["Hostname"]
                ip_addr  = node.attrs["Status"]["Addr"]
                slog.info("Swarm node: %s (%s)" % (hostname, ip_addr))
                docker_api_base_url = "tcp://%s:4243" % ip_addr
                slog.debug("docker_api_base_url: %s" % docker_api_base_url) 
                swarm_client = docker.DockerClient(base_url=docker_api_base_url)
                swarm_node_conn_list.append(swarm_client)
                # TODO: add this node object to core_node
                ##
                ##
                ##
                ##
                ##
                ##
                ## 
            except Exception as ex:
                slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
                slog.error("%s" % str(traceback.format_exc()))
                slog.error("This swarm server(%s) is unavailable" % docker_api_base_url) 

        slog.debug("swarm node(%s): %s" % (len(swarm_node_conn_list), swarm_node_conn_list))
        return swarm_node_conn_list 
    except Exception as ex:
        slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
        slog.error("%s" % str(traceback.format_exc()))
        return None 


def monitor_thr(models_active):
    slog.debug("models_active: %s" % models_active)

    swarm_manager_address = get_swarm_manager_address() 
    docker_api_base_url = "tcp://%s:4243" % swarm_manager_address 
    slog.debug("docker_api_base_url: %s" % docker_api_base_url)
    my_client = docker.DockerClient(base_url=docker_api_base_url)

    worker_node_connected = False 
    swarm_node_conn_list = []
    while True:
        try: 
            # To extract swarm node connection list from swarm manager
            if worker_node_connected == False:
                swarm_node_conn_list = get_worker_conn_list(my_client) 
                worker_node_connected = True

            # To extract network list from core_network model  
            network_list = Network.objects.all()
            for network in network_list:
                try: 
                    # To get docker network information from swarm manager
                    slog.debug("network.name: %s" % network.name)
                    for swarm_client in swarm_node_conn_list:
                        try:
                            docker_net = swarm_client.networks.get(network.name)
                            container_list = docker_net.attrs['Containers'].values()

                            # To extract ip address and container name which uses its network
                            for container in container_list:
                                slog.debug("Container name: %s" % container["Name"])
                                slog.debug("IPv4          : %s" % container["IPv4Address"]) 
                                ip_addr = transform_ip_addr(container["IPv4Address"]) 

                                # To search instance name with container["Name"]
                                instance = search_instance(container["Name"])
                                if instance is None:
                                    slog.debug("%s is not container which is created by XOS" % container["Name"])
                                    continue 

                                # Check if same port tuple is on core_port.
                                port_info = search_port(network, instance)
                                if port_info is not None:  # port already exists
                                    if port_info.ip == ip_addr: 
                                        continue  # Nothing to do:
                                    else :
                                        # renew port information
                                        port_info.ip =  ip_addr
                                        port_info.mac = container["MacAddress"]
                                        port_info.save()
                                        slog.debug("(%s, %s) renew port information (%s)" % 
                                                    (instance.instance_name, network.name, port_info.ip))

                                slog.debug("instance name: %s   instance_id: %s   network_id: %s" % 
                                            (instance.instance_name, instance.id, network.id))
                                # To insert port tuple on core_port model 
                                new_port = Port()
                                new_port.ip      = ip_addr
                                new_port.mac     = container["MacAddress"]
                                new_port.leaf_model_name = "Port"
                                new_port.xos_created = True
                                new_port.instance_id = instance.id
                                new_port.network_id  = network.id
                                new_port.save() 
                                slog.debug("(%s, %s) renew port information (%s)" % 
                                            (instance.instance_name, network.name, new_port.ip)) 
                        except Exception as ex:
                            slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
                            slog.error("%s" % str(traceback.format_exc())) 
                except Exception as ex:
                    slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
                    slog.error("%s" % str(traceback.format_exc()))
        except Exception as ex:
            slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
            slog.error("%s" % str(traceback.format_exc()))
            # reconnect to docker api server on swarm manager node
            my_client = docker.DockerClient(base_url=docker_api_base_url)
            worker_node_connected = False 
        time.sleep(7)
