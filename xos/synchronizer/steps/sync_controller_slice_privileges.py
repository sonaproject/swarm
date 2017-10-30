
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
from synchronizers.new_base.ansible_helper import *
from xos.logger import observer_logger as logger
from synchronizers.new_base.modelaccessor import *

import synchronizers.swarm.swarmlog as slog

#class SyncControllerSlicePrivileges(SwarmSyncStep):
class SyncControllerSlicePrivileges(SyncStep):
    provides=[SlicePrivilege]
    requested_interval=0
    observes=ControllerSlicePrivilege
    playbook = 'sync_controller_users.yaml'

    def map_sync_inputs(self, controller_slice_privilege):
        slog.info("controller_slice_privilege: %r" % controller_slice_privilege) 
        if not controller_slice_privilege.controller.admin_user:
            slog.info("controller %r has no admin_user, skipping" % controller_slice_privilege.controller)
            return

        template = os_template_env.get_template('sync_controller_users.yaml')
        slog.info("sync_controller_users.yaml --> template: %s" % template) 
        roles = [controller_slice_privilege.slice_privilege.role.role]
        # setup user home slice roles at controller 
        if not controller_slice_privilege.slice_privilege.user.site:
            slog.info('Sliceless user %s' % controller_slice_privilege.slice_privilege.user.email)
            raise Exception('Sliceless user %s'%controller_slice_privilege.slice_privilege.user.email)
        else:
            swarm_manager_url = controller_slice_privilege.controller.auth_url
            slog.info("swarm_manager_url: %s" % swarm_manager_url)
            (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
            slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (swarm_manager_address, docker_registry_port))

            user_fields = {
                        'swarm_manager_address' : swarm_manager_address,
                        'admin_user': controller_slice_privilege.controller.admin_user,
                        'ansible_tag':'%s@%s@%s'%(
                                    controller_slice_privilege.slice_privilege.user.email.replace('@','-at-'),
                                    controller_slice_privilege.slice_privilege.slice.name,
                                    controller_slice_privilege.controller.name)
                        }

            slog.info("user_fields: %s" % user_fields) 

            return user_fields

    def map_sync_outputs(self, controller_slice_privilege, res):
        slog.info("res: %s" % res)
        controller_slice_privilege.role_id = res[0]['id']
        controller_slice_privilege.save()

    def delete_record(self, controller_slice_privilege):
        controller_register = json.loads(controller_slice_privilege.controller.backend_register)
        slog.info("controller_register: %s" % controller_register)
        if (controller_register.get('disabled',False)):
                raise InnocuousException('Controller %s is disabled'%controller_slice_privilege.controller.name)

