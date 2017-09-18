import os
import base64
#from synchronizers.swarm.swarmsyncstep import SwarmSyncStep
from synchronizers.new_base.syncstep import SyncStep
from xos.logger import observer_logger as logger
from synchronizers.new_base.modelaccessor import *

import synchronizers.swarm.swarmlog as slog

#class SyncRoles(SwarmSyncStep):
class SyncRoles(SyncStep):
    provides=[Role]
    requested_interval=0
    observes=[SiteRole,SliceRole,ControllerRole]

    def sync_record(self, role):
        slog.info("role: %r" % role) 
        slog.info("role.enacted: %s" % role.enacted) 
        if not role.enacted:
            controllers = Controller.objects.all()
            slog.info("controllers: %s" % controllers) 
            for controller in controllers:
                slog.info("controller: %s" % controller)
            role.save()
 

