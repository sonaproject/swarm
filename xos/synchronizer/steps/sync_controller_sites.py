import os
import base64
from synchronizers.swarm.swarmsyncstep import SwarmSyncStep
from synchronizers.new_base.syncstep import *
from synchronizers.new_base.ansible_helper import *
import json
from synchronizers.new_base.modelaccessor import *
from xos.logger import observer_logger as logger

import synchronizers.swarm.swarmlog as slog 

class SyncControllerSites(SwarmSyncStep):
    requested_interval=0
    provides=[Site]
    observes=ControllerSite
    playbook = 'sync_controller_sites.yaml'

    def fetch_pending(self, deleted=False):
        lobjs = super(SyncControllerSites, self).fetch_pending(deleted)
        slog.info("lobjs: %r" % lobjs) 

        slog.info("deleted: %s" % deleted)
        if not deleted:
            # filter out objects with null controllers
            lobjs = [x for x in lobjs if x.controller]
            slog.info("lobjs: %r" % lobjs)

        return lobjs

    def map_sync_inputs(self, controller_site):
        swarm_manager_url = controller_site.controller.auth_url
        slog.info("swarm_manager_url: %s" % swarm_manager_url)
        (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
        slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (swarm_manager_address, docker_registry_port))

        input_fields = {
                        'swarm_manager_address' : swarm_manager_address,
                        'admin_user': controller_site.controller.admin_user,
                        'ansible_tag': '%s@%s'%(
                                        controller_site.site.login_base,
                                        controller_site.controller.name), # name of ansible playbook
                        'tenant_description': controller_site.site.name
                        }

        slog.info("input_fields: %s" % input_fields) 

        return input_fields

    def map_sync_outputs(self, controller_site, res):
        controller_site.tenant_id = ' '
        controller_site.backend_status = '1 - OK'
        controller_site.save()

    def delete_record(self, controller_site):
        slog.info("controller_site: %r" % controller_site) 
        controller_register = json.loads(controller_site.controller.backend_register)
        slog.info("controller_register: %s" % controller_register) 
        if (controller_register.get('disabled',False)):
            slog.info('Controller %s is disabled'%controller_site.controller.name) 
            raise InnocuousException('Controller %s is disabled'%controller_site.controller.name)

