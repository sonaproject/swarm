import os
import base64
from synchronizers.swarm.swarmsyncstep import SwarmSyncStep
from synchronizers.new_base.syncstep import *
from synchronizers.new_base.ansible_helper import *
from xos.logger import observer_logger as logger
from synchronizers.new_base.modelaccessor import *

import synchronizers.swarm.swarmlog as slog

class SyncControllerSlices(SwarmSyncStep):
    provides=[Slice]
    requested_interval=0
    observes=ControllerSlice
    playbook='sync_controller_slices.yaml'

    def map_sync_inputs(self, controller_slice):
        slog.info("sync'ing slice controller %s" % controller_slice)

        if not controller_slice.controller.admin_user:
            slog.info("controller %r has no admin_user, skipping" % controller_slice.controller)
            return

        slog.info("controller_slice.slice.creator.id: %s    controller_slice.controller.id: %s" % (
                    controller_slice.slice.creator.id, controller_slice.controller.id))
        controller_users = ControllerUser.objects.filter(user_id=controller_slice.slice.creator.id,
                                                             controller_id=controller_slice.controller.id)
        if not controller_users:
            slog.info("slice createor %s has not accout at controller %s" % (
                        controller_slice.slice.creator, controller_slice.controller.name))
            raise Exception("slice createor %s has not accout at controller %s" % (
                        controller_slice.slice.creator, controller_slice.controller.name))
        else:
            controller_user = controller_users[0]

        max_instances=int(controller_slice.slice.max_instances)
        slog.info("controller_slice.slice.max_instances: %s" % controller_slice.slice.max_instances)

        swarm_manager_url = controller_slice.controller.auth_url
        (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
        slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (swarm_manager_address, docker_registry_port)) 

        tenant_fields = {
                        'swarm_manager_address' : swarm_manager_address, 
                        'admin_user': controller_slice.controller.admin_user,
                        'ansible_tag':'%s@%s' % (
                                                controller_slice.slice.name,
                                                controller_slice.controller.name)
                        } 
        slog.info("tenant_fields: %s" % tenant_fields) 

        return tenant_fields


    def map_sync_outputs(self, controller_slice, res):
        controller_slice.backend_status = 'OK'
        controller_slice.backend_code   = 1
        controller_slice.save() 


    def map_delete_inputs(self, controller_slice):
        slog.info("controller_slice: %r" % controller_slice) 
        controller_users = ControllerUser.objects.filter(user_id=controller_slice.slice.creator.id,
                                                          controller_id=controller_slice.controller.id)
        slog.info("controller_slice.slice.creator.id: %s   controller_slice.controller.id: %s" % (
                    controller_slice.slice.creator.id, controller_slice.controller.id))

        if not controller_users:
            slog.info("slice createor %s has not accout at controller %s" % (
                        controller_slice.slice.creator, controller_slice.controller.name))
            raise Exception("slice createor %s has not accout at controller %s" % (
                        controller_slice.slice.creator, controller_slice.controller.name))
        else:
            controller_user = controller_users[0]

        swarm_manager_url = controller_slice.controller.auth_url
        (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
        tenant_fields = { 
                        'swarm_manager_address' : swarm_manager_address, 
                        'admin_user': controller_slice.controller.admin_user,
                        'ansible_tag':'%s@%s' % (
                                                controller_slice.slice.name,
                                                controller_slice.controller.name), 
                        'delete': True 
                        }
        slog.info("tenant_fields: %s" % tenant_fields)

        return tenant_fields
