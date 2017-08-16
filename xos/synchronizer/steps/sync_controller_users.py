import os
import base64
from synchronizers.swarm.swarmsyncstep import SwarmSyncStep
from synchronizers.new_base.syncstep import *
from synchronizers.new_base.ansible_helper import *
from xos.logger import observer_logger as logger
from synchronizers.new_base.modelaccessor import *

import synchronizers.swarm.swarmlog as slog

class SyncControllerUsers(SwarmSyncStep):
    provides=[User]
    requested_interval=0
    observes=ControllerUser
    playbook='sync_controller_users.yaml'

    def map_sync_inputs(self, controller_user):
        slog.debug("controller user: %r" % controller_user)
        if not controller_user.controller.admin_user:
            slog.info("controller %r has no admin_user, skipping" % controller_user.controller)
            return

        # All users will have at least the 'user' role at their home site/tenant.
        # We must also check if the user should have the admin role

        roles = ['user']

        # setup user home site roles at controller
        if not controller_user.user.site:
            raise Exception('Siteless user %s'%controller_user.user.email)
        else:
            swarm_manager_url = controller_user.controller.auth_url
            slog.info("swarm_manager_url: %s" % swarm_manager_url)
            (swarm_manager_address, docker_registry_port) = swarm_manager_url.split(':')
            slog.info("swarm_manager_address: %s    docker_registry_port: %s" % (
                        swarm_manager_address, docker_registry_port))

            user_fields = {
                        'swarm_manager_address' : swarm_manager_address,
                        'admin_user': controller_user.controller.admin_user,
                        'ansible_tag':'%s@%s'%(
                                            controller_user.user.email.replace('@','-at-'),
                                            controller_user.controller.name)  # name of ansible playbook
                        }
        slog.info("user_fields: %s" % user_fields)
        return user_fields

    def map_sync_outputs(self, controller_user, res):
        controller_user.backend_status = '1 - OK'
        controller_user.save()

    def delete_record(self, controller_user):
        slog.info("Nothing to delete (%r)" % controller_user) 
        pass

