import os
import base64
import socket
import threading
import time

from synchronizers.swarm.swarmsyncstep import SwarmSyncStep
from synchronizers.new_base.ansible_helper import *
from synchronizers.new_base.syncstep import *
from xos.logger import observer_logger as logger
from synchronizers.new_base.modelaccessor import *

import synchronizers.swarm.swarmlog as slog

RESTAPI_HOSTNAME = socket.gethostname()
RESTAPI_PORT = "8000"

class SyncInstances(SwarmSyncStep):
    provides = [Instance]
    requested_interval = 0
    observes = Instance
    playbook = 'sync_instances.yaml' 

    # XOS-Core has specific block period time 128 seconds.
    #   - If you changed any information of tenant(or instance), 
    #   - then XOS-Core make a block all updating-operation for 128 seconds.
    # In general operating situation, This 128-second blocking time is not problerm.
    # But You need a fast operating & its response to show a DEMO to someone in real-time,
    # This method is helpful in such case.
    # If you don't need to get fast response from XOS-Core, Don't use following method.
    def update_instance_with_ssh(self, inst_id):
        try: 
            import subprocess
            import shlex

            new_inst = Instance.objects.get(id=inst_id)

            controller = new_inst.node.site_deployment.controller
            swarm_manager_url = controller.auth_url
            (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
            slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (swarm_manager_address, docker_registry_port)) 
            volume_mount_opt = "--mount-add type=bind,src=/opt/xos/instance_volume/%s,dst=%s" % (new_inst.id, new_inst.volumes)

            ## DOCKER SERVICE UPDATE
            ssh_cmd = "ssh root@%s   docker service update  --force  %s  %s" % (
                        swarm_manager_address,  volume_mount_opt, new_inst.instance_name)
            slog.debug("SSH CMD: %s" % ssh_cmd) 
            popen = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            (stdoutdata, stderrdata) = popen.communicate() 
            slog.debug("popen result: %s    etc data: %s" % (stdoutdata, stderrdata))

            ## DOCKER SERVICE STATUS
            ssh_cmd = "ssh root@%s  docker service ps %s" % (swarm_manager_address, new_inst.instance_name)
            slog.debug("SSH CMD: %s" % ssh_cmd) 
            popen = subprocess.Popen(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            (stdoutdata, stderrdata) = popen.communicate() 
            slog.debug("popen result: %s    etc data: %s" % (stdoutdata, stderrdata))
        except Exception as ex:
            slog.info("Exception: %s" % ex)

        return 0


    def update_instance(self, instance):
        slog.info("[THREAD] instance_name: %s   Thread: %s    instance.updated: %s" % (
                    instance.instance_name, threading.current_thread().name, instance.updated)) 
        time.sleep(10)

        try:
            inst_id = instance.id
            slog.debug("[THREAD] inst_id          : %s" % inst_id)
            old_update = 0

            for idx in range(1, 100, 1):
                slog.debug("[THREAD] idx: %s" % idx)
                new_inst = Instance.objects.get(id=inst_id)

                if old_update == 0:
                    old_update = new_inst.updated
                slog.debug("[THREAD] updated(old)     : %s" % time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(old_update)))

                if (new_inst.volumes is not None) and (new_inst.instance_name is not None):
                    if (len(new_inst.volumes) > 2) and  (len(new_inst.instance_name) > 2):
                        slog.debug("[THREAD] instance_name    : %s  (%s)" % (new_inst.instance_name, len(new_inst.instance_name)))
                        slog.debug("[THREAD] volumes          : %s  (%s)" % (new_inst.volumes ,      len(new_inst.volumes )))

                        if idx == 1:
                            slog.debug("Call update_instance_with_ssh()")
                            self.update_instance_with_ssh(inst_id)

                        new_inst.numberCores = idx
                        new_inst.updated     = time.time()
                        slog.debug("[THREAD] updated to renew : %s (%s)" % (
                                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(new_inst.updated)), 
                                    new_inst.updated))
                        new_inst.save(update_fields=['updated', 'numberCores'])

                        time.sleep(1)

                        clone_inst = Instance.objects.get(id=inst_id)
                        clone_inst.save(update_fields=['numberCores'])
                        slog.debug("[THREAD] updated          : %s (%s)" % (
                                    time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(clone_inst.updated)), 
                                    clone_inst.updated))
                        if clone_inst.updated == old_update:
                            slog.debug("[THREAD] updated date was not changed. Nothing is executed. Waiting 5 seconds.")
                            time.sleep(5)
                        else:
                            slog.debug("[THREAD] updated date was changed. Swarm synchronizer will run ansible")
                            return 
        except Exception as ex:
            slog.info("[THREAD] Exception: %s" % str(ex.args)) 
            slog.info("[THREAD] Exception: %s" % str(ex)) 


    def chk_svc_exist(self, instance, swarm_manager_address):
        duplicated_flag = False
        try:
            instance_name = '%s-%d' % (instance.slice.name, instance.id)
            slog.debug("Service name to chkeck: %s" % instance_name)

            import docker
            docker_api_base_url = "tcp://%s:4243" % swarm_manager_address
            slog.debug("Docker API Base URL: %s" % docker_api_base_url)
            my_client = docker.DockerClient(base_url=docker_api_base_url)
            swarm_svc = my_client.services.get(instance_name)

            slog.debug("swarm_svc.id     : %s" % swarm_svc.id)
            slog.debug("swarm_svc.name   : %s" % swarm_svc.name)
            slog.debug("swarm_svc.attrs  : %s" % swarm_svc.attrs)
        except Exception as ex:
            slog.debug("Exception: %s" % str(ex.args))
            slog.debug("Exception: %s" % str(ex))
            duplicated_flag = False  # There is no same service.
        else:
            duplicated_flag = True   # There is same service.
        return duplicated_flag 


    def fetch_pending(self, deletion=False):
        slog.info("begin fetch_pending(%s)" % deletion)
        objs = super(SyncInstances, self).fetch_pending(deletion)
        slog.info("objs: %s" % objs) 
        objs = [x for x in objs if x.isolation == "vm"]
        slog.info("vm objs: %s" % objs) 
        return objs 

    def map_sync_inputs(self, instance): 
        slog.debug("instance: %s    slice: %s" % (instance, instance.slice.name))
        
        controller = instance.node.site_deployment.controller 
        swarm_manager_url = controller.auth_url
        slog.info("swarm_manager_url: %s" % swarm_manager_url)
        (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
        slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (
                    swarm_manager_address, docker_registry_port)) 

        # check if this service is created already on swarm cluster.
        duplicated_flag = self.chk_svc_exist(instance, swarm_manager_address)
        if duplicated_flag is True:
            swarm_service_update_flag = True 

        ## if instance.instance_uuid is not None, 
        ## then This method will update the instance with new configuration.
        swarm_service_update_flag = False
        if instance.instance_uuid is not None:
            if len(instance.instance_uuid) > 2:
                swarm_service_update_flag = True 

		## To get volume information 
        if instance.volumes:
            slog.debug("instance.volumes: %s" % instance.volumes)
            if len(instance.volumes) < 2:
                slog.debug("instance.volumes(%s) is too short" % instance.volumes)
                instance.volumes = "/usr/local/etc/haproxy"  ## Default value
        else:
            slog.debug("instance.volumes is None")
            instance.volumes = "/usr/local/etc/haproxy"  ## Default value 
        slog.debug("instance.volumes: %s" % instance.volumes) 

        ## set options for volume mounting 
        ##   --mount type=bind,src=/opt/xos/instance_volume/1,dst=/usr/local/etc/haproxy  
        volume_mount_opt = " "
        if swarm_service_update_flag is True:
            volume_mount_opt = "--mount-add type=bind,src=/opt/xos/instance_volume/%s,dst=%s" % (
                                instance.id, instance.volumes) 
        else:
            volume_mount_opt = "--mount type=bind,src=/opt/xos/instance_volume/%s,dst=%s" % (
                                instance.id, instance.volumes) 
        slog.debug("volume_mount_opt: %s" % volume_mount_opt)

        # sanity check - make sure model_policy for slice has run
        if ((not instance.slice.policed) or (instance.slice.policed < instance.slice.updated)):
            slog.info("Instance %s waiting on Slice %s to execute model policies" % (
                        instance, instance.slice.name))
            raise DeferredException(
                "Instance %s waiting on Slice %s to execute model policies" % (
                        instance, instance.slice.name))

        # sanity check - make sure model_policy for all slice networks have run
        for network in instance.slice.ownedNetworks.all():
            slog.info("network: %s" % network)
            if ((not network.policed) or (network.policed < network.updated)):
                slog.info("Instance %s waiting on Network %s to execute model policies" % (
                            instance, network.name))
                raise DeferredException(
                    "Instance %s waiting on Network %s to execute model policies" % (
                            instance, network.name))

        nics = []

        # handle ports the were created by the user
        for port in Port.objects.filter(instance_id=instance.id):
            slog.debug("Port.port_id: %s" % port.port_id)
            if not port.port_id:
                raise DeferredException("Instance %s waiting on port %s" % (instance, port))
            nics.append({"kind": "port", "value": port.port_id, "network": port.network})

        # we want to exclude from 'nics' any network that already has a Port
        existing_port_networks = [port.network for port in Port.objects.filter(instance_id=instance.id)]
        existing_port_network_ids = [x.id for x in existing_port_networks]
        slog.debug("existing_port_network_id list: %s" % str(existing_port_network_ids))

        networks = [ns.network for ns in NetworkSlice.objects.filter(slice_id=instance.slice.id) if
                    ns.network.id not in existing_port_network_ids]
        networks_ids = [x.id for x in networks]
        slog.debug("networks id list: %s" % str(networks_ids))
        controller_networks = ControllerNetwork.objects.filter(
            controller_id=instance.node.site_deployment.controller.id)
        controller_networks = [x for x in controller_networks if x.id in networks_ids]
        slog.debug("controller_network list: %s" % str(controller_networks))

        swarm_network = ""
        for network in networks:
            slog.debug("networkd.id: %s(%s, %s)  controller.id: %s" % (
                        network.id, network.name, network.subnet, 
                        instance.node.site_deployment.controller.id))
            if not ControllerNetwork.objects.filter(
                                            network_id=network.id,
                                            controller_id=instance.node.site_deployment.controller.id).exists():
                raise DeferredException(
                                "Instance %s Private Network %s lacks ControllerNetwork object" % (
                                instance, network.name))
            swarm_network += " --network %s " % network.name
        slog.debug("swarm_network: %s" % swarm_network)

        image_name = None
        controller_images = instance.image.controllerimages.all()
        controller_images = [x for x in controller_images if
                             x.controller_id == instance.node.site_deployment.controller.id]
        if controller_images:
            image_name = controller_images[0].image.name
            slog.info("using image from ControllerImage object: " + str(image_name))

        host_filter = instance.node.name.strip()
        slog.info("instance.node.name: %s" % instance.node.name)

        instance_name = '%s-%d' % (instance.slice.name, instance.id)
        slog.info("instance.slice.name: %s    instance.id: %s    instance_name: %s" % (
                    instance.slice.name, instance.id, instance_name))
        self.instance_name = instance_name

        input_fields = {
                        'swarm_manager_address' : swarm_manager_address,
                        'swarm_service_name'    : instance_name,
                        'network_name'          : swarm_network,
                        'replicas'              : "--replicas 1",              ## default value
                        'restart_condition'     : "--restart-condition on-failure",  ## default value
                        'volume'                : volume_mount_opt,
                        'docker_registry_port'  : docker_registry_port,
                        'image_name'            : instance.image.name,
                        'image_tag'             : instance.image.tag, 
                        'ansible_tag'           : instance_name,
                        'delete'                : False,
                        # 'duplicated'            : duplicated_flag,
                        'update'                : swarm_service_update_flag
                        }

        slog.info("input_fields: %s" % input_fields)

        if swarm_service_update_flag is False:
            slog.info("swarm_service_update_flag is %s, so I will update once more" % swarm_service_update_flag) 
            try:
                my_thr = threading.Thread(target=self.update_instance, args=(instance,))
                my_thr.start()
            except Exception as ex:
                slog.log_exc("update_instance Thread creation failed - %s" % ex)

        return input_fields

    def map_sync_outputs(self, instance, res):
        slog.info("ansible playbook ressult: %s" % str(res))
        slog.info("ansible playbook ressult[1][stdout]: %s" % str(res[1]['stdout']))

        res_stdout = res[1]['stdout']
        json_content = json.loads(res_stdout)
        slog.info("json_content: %s" % str(json_content))
        instance.instance_id = json_content[0]['Spec']["Name"]
        slog.info("instance.instance_id: %s" % str(instance.instance_id))
        instance.instance_uuid = json_content[0]['ID']
        slog.info("instance.instance_uuid: %s" % str(instance.instance_uuid))

        controller = instance.node.site_deployment.controller
        swarm_manager_url = controller.auth_url
        (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
        slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (
                    swarm_manager_address, docker_registry_port))

        try: 
            instance.ip = socket.gethostbyname(swarm_manager_address)
        except Exception,e:
            slog.info(str(e)) 
            slog.info("hostname(%s) resolution fail" % swarm_manager_address)
            pass 

        instance.instance_name = self.instance_name
        instance.save()

    def map_delete_inputs(self, instance):
        controller_register = json.loads(instance.node.site_deployment.controller.backend_register)
        slog.info("controller_register: %s" % controller_register)

        if (controller_register.get('disabled', False)):
            slog.info('Controller %s is disabled' % instance.node.site_deployment.controller.name)
            raise InnocuousException('Controller %s is disabled' % instance.node.site_deployment.controller.name)

        instance_name = '%s-%d' % (instance.slice.name, instance.id)
        slog.info("instance_name: %s" % instance_name)

        controller = instance.node.site_deployment.controller
        slog.info("controller: %s" % controller) 
        swarm_manager_url = controller.auth_url
        slog.info("swarm_manager_url: %s" % swarm_manager_url)
        (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
        slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (swarm_manager_address, docker_registry_port))

        input = {
                'swarm_manager_address' : swarm_manager_address,
                'swarm_service_name'    : instance_name,
                'ansible_tag'           : instance_name,
                'delete'                : True
                }
        return input
