
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
 

