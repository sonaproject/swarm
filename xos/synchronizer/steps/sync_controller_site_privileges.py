
# Copyright 2017-present Open Networking Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os
import base64
import json
#from synchronizers.swarm.swarmsyncstep import SwarmSyncStep
#from synchronizers.new_base.syncstep import SyncStep
from synchronizers.new_base.syncstep import *
from xos.logger import observer_logger as logger
from synchronizers.new_base.ansible_helper import *
from synchronizers.new_base.modelaccessor import *

import synchronizers.swarm.swarmlog as slog 

#class SyncControllerSitePrivileges(SwarmSyncStep):
class SyncControllerSitePrivileges(SyncStep):
    provides=[SitePrivilege]
    requested_interval=0
    observes=ControllerSitePrivilege
    playbook='sync_controller_users.yaml'

    def map_sync_inputs(self, controller_site_privilege):
        slog.info("begin map_sync_input()") 
        controller_register = json.loads(controller_site_privilege.controller.backend_register)
        if not controller_site_privilege.controller.admin_user:
            slog.info("controller %r has no admin_user, skipping" % controller_site_privilege.controller)
            return

        roles = [controller_site_privilege.site_privilege.role.role]
        slog.info("roles: %s" % roles) 
        # setup user home site roles at controller 
        if not controller_site_privilege.site_privilege.user.site:
            slog.info("Siteless user %s" % controller_site_privilege.site_privilege.user.email)
            raise Exception('Siteless user %s'%controller_site_privilege.site_privilege.user.email)
        else:
            swarm_manager_url = controller_site_privilege.controller.auth_url
            slog.info("swarm_manager_url: %s" % swarm_manager_url)
            (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
            slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (
                        swarm_manager_address, 
                        docker_registry_port)) 

            user_fields = {
                            'swarm_manager_address' : swarm_manager_address, 
                            'name': controller_site_privilege.site_privilege.user.email,
                            'admin_user': controller_site_privilege.controller.admin_user,
                            'ansible_tag':'%s@%s' % (
                                            controller_site_privilege.site_privilege.user.email.replace('@','-at-'),
                                            controller_site_privilege.controller.name)
                            } 
        slog.info("user_fields: %s" % user_fields)

        return user_fields


    def map_sync_outputs(self, controller_site_privilege, res):
        # results is an array in which each element corresponds to an 
        # "ok" string received per operation. If we get as many oks as
        # the number of operations we issued, that means a grand success.
        # Otherwise, the number of oks tell us which operation failed.
        slog.info("res: %s" % res) 
        controller_site_privilege.role_id = res[0]['id']
        controller_site_privilege.save()


    def delete_record(self, controller_site_privilege):
        controller_register = json.loads(controller_site_privilege.controller.backend_register)
        slog.info("controller_register: %s" % controller_register)

        if (controller_register.get('disabled',False)):
            slog.info("Controller %s is disabled" % controller_site_privilege.controller.name) 
            raise InnocuousException('Controller %s is disabled'%controller_site_privilege.controller.name)

        slog.info("Nothing to do on Swarm cluster") 
        pass

