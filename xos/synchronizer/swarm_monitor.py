import os
import base64
import json
import time
import sys, traceback

from xos.logger import observer_logger as logger
from synchronizers.new_base.modelaccessor import *

import synchronizers.swarm.swarmlog as slog 

import docker 


def search_port(network, instance):
    try:
        slog.debug("network: %s   instance: %s" % (network.name, instance.instance_name))
        port = Port.objects.filter(network_id=network.id, instance_id=instance.id)
        slog.debug("(%s, %s)  port object count: %s" % (network.name, instance.instance_name, len(port)))
        if len(port) == 0:
            slog.debug("(%s, %s) does not exist, I would create new port tuple" % (network.name, instance.instance_name))
            return None
        slog.debug("(%s, %s) Port already exists (%s)" % (network.name, instance.instance_name, port[0].ip))
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


def get_worker_conn_list(docker_client):
    swarm_node_conn_list = []
    try: 
        swarm_nodes = docker_client.nodes.list()
        for node in swarm_nodes:
            # To extract ip address, hostname of swarm node
            try:
                hostname = node.attrs["Description"]["Hostname"]
                ip_addr  = node.attrs["Status"]["Addr"]
                slog.info("Swarm node: %s (%s)" % (hostname, ip_addr))
                docker_api_base_url = "tcp://%s:4243" % ip_addr
                slog.debug("docker_api_base_url: %s" % docker_api_base_url) 
                swarm_client = docker.DockerClient(base_url=docker_api_base_url)
                swarm_node_conn_list.append({ "node_id": node.id, "hostname": hostname, "swarm_client": swarm_client }) 
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

def make_container_exec(swarm_client_dict, instance, container_id):
    try:
        # { "node_id": node.id, "hostname": nostname, "swarm_client": swarm_client }
        slog.debug("(instance: %s)  swarm_client: %s (%s)   container_id: %s" % 
                    (instance.instance_name, swarm_client_dict["hostname"], 
                    swarm_client_dict["node_id"], container_id))
        swarm_client = swarm_client_dict["swarm_client"]
        container = swarm_client.containers.get(container_id)
        userData = json.loads(instance.userData)
        slog.debug("(instance: %s)  container name: %s   command: %s" % 
                    (instance.instance_name, container.name, userData["command"])) 
        exec_result = container.exec_run(userData["command"])
        exec_result = exec_result.strip('\n')
        slog.debug("%s container exec_result: %s" % (container.name, exec_result))
        userData['result'] = exec_result
        userData['update_date'] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time())) 
        userData['node_name'] = swarm_client_dict["hostname"]
        userData['node_id'] = swarm_client_dict["node_id"]
        instance.userData = json.dumps(userData)
        instance.save(update_fields=['userData']) 
    except Exception as ex:
        slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
        slog.error("%s" % str(traceback.format_exc())) 
    return None


def get_svc_status(swarm_node_conn_list, instance, node_id, container_id):
    slog.debug("(instance: %s) node_id: %s   container_id: %s" % 
                (instance.instance_name, node_id, container_id))
    try:
        slog.debug("swarm client number: %s" % len(swarm_node_conn_list))
        for swarm_client_dict in swarm_node_conn_list:
            slog.debug("node search:  %s  vs  %s" % (swarm_client_dict["node_id"], node_id))
            if swarm_client_dict["node_id"] == node_id:
                # Run 'docker exec -it contain_name_a  service haproxy status'
                slog.debug("Container command execution on node(%s)" % node_id)
                make_container_exec(swarm_client_dict, instance, container_id)
                return None
        slog.error("Could not find node (%s)" % node_id)
    except Exception as ex:
        slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
        slog.error("%s" % str(traceback.format_exc())) 
    return None


def get_svc_info(docker_client, swarm_node_conn_list):
    task_filter = {'desired-state': 'running'} 
    instance_list = Instance.objects.all()
    for instance in instance_list:
        try:
            slog.debug("instance: %s" % instance.instance_name)
            docker_svc = docker_client.services.get(instance.instance_name)
            docker_task_list = docker_svc.tasks(task_filter)
            if len(docker_task_list) == 0:
                slog.debug("service(%s) does not have a running container" % instance.instance_name)                
                instance.backend_status = "2 - NOK : Docker container is not running"
                instance.save(update_fields=['backend_status'])
                continue
            if instance.backend_status != "1 - OK":
                instance.backend_status = "1 - OK"
                instance.save(update_fields=['backend_status'])
            docker_task = docker_task_list[0]
            slog.debug("(instance: %s) docker task information: %s" % (instance.instance_name, docker_task))
            slog.debug("(instance: %s) Container Status : %s" % 
                            (instance.instance_name, docker_task["Status"]["State"])) 
            slog.debug("(instance: %s) NodeID : %s" % (instance.instance_name, docker_task["NodeID"]))
            get_svc_status(swarm_node_conn_list, instance, docker_task["NodeID"],
                            docker_task["Status"]["ContainerStatus"]["ContainerID"])
            attached_network_list = docker_task["NetworksAttachments"]
            if len(attached_network_list) == 0:
                slog.debug("Instance(%s) doesn't have a network" % instance.instance_name)
                continue
            for attached_network in attached_network_list:
                network_name = attached_network["Network"]["Spec"]["Name"]
                ip_addr      = transform_ip_addr(attached_network["Addresses"][0])
                slog.debug("(instance: %s) Network Name: %s" % (instance.instance_name, network_name))
                slog.debug("(instance: %s) IP Address  : %s" % (instance.instance_name, ip_addr)) 
                # To search network_id from DB,  
                network = Network.objects.get(name=network_name) 
                if network is None:
                    slog.info("%s does not exist on DB(core_networ tabke)" % network_name) 
                    continue 

                # To check if same port tuple is on core_port.
                port_info = search_port(network, instance)
                if port_info is None: 
                    # To insert port tuple on core_port model
                    new_port = Port() 
                    new_port.ip          = ip_addr
                    new_port.leaf_model_name = "Port"
                    new_port.xos_created = True
                    new_port.instance_id = instance.id
                    new_port.network_id  = network.id
                    new_port.save() 
                    slog.debug("(%s, %s) insert port information (%s) into core_port table on DB" % 
                                (instance.instance_name, network.name, ip_addr)) 
                else: # port already exists 
                    if port_info.ip == ip_addr:
                        slog.debug("port(%s) is in DB already" % ip_addr)
                        continue  # Nothing to do:
                    else :
                        # update port information
                        port_info.ip =  ip_addr
                        port_info.save()
                        slog.debug("(%s, %s) update port information (%s)" %
                                    (instance.instance_name, network.name, port_info.ip)) 
        except Exception as ex:
            slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
            slog.error("%s" % str(traceback.format_exc()))
            instance.backend_status = "2 - NOK : %s service is not running (%s)" % (instance.instance_name, str(ex))
            instance.save(update_fields=['backend_status'])


def monitor_thr(models_active):
    slog.debug("models_active: %s" % models_active)

    swarm_manager_address = get_swarm_manager_address() 
    docker_api_base_url = "tcp://%s:4243" % swarm_manager_address 
    slog.debug("docker_api_base_url: %s" % docker_api_base_url)
    docker_client = docker.DockerClient(base_url=docker_api_base_url)

    worker_node_connected = False 
    swarm_node_conn_list = []
    while True:
        try: 
            # To extract swarm node connection list from swarm manager
            if worker_node_connected == False:
                swarm_node_conn_list = get_worker_conn_list(docker_client) 
                worker_node_connected = True 
            get_svc_info(docker_client, swarm_node_conn_list) 
        except Exception as ex:
            slog.error("Exception: %s   %s   %s" % (type(ex), str(ex), ex.args))
            slog.error("%s" % str(traceback.format_exc()))
            # reconnect to docker api server on swarm manager node
            docker_client = docker.DockerClient(base_url=docker_api_base_url)
            worker_node_connected = False 
        time.sleep(7)
