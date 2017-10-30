
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


from synchronizers.new_base.modelaccessor import *
from collections import defaultdict
from synchronizers.new_base.policy import Policy

import synchronizers.swarm.swarmlog as slog

class NetworkPolicy(Policy):
    model_name = "Network"

    def handle_create(self, network):
        slog.debug("network object: %s" % str(network))
        return self.handle_update(network)

    def handle_update(self, network):
        slog.debug("network.name: %s   id: %s" % (network.name, network.id))

        expected_controllers =  Controller.objects.all()
        slog.debug("(network.name: %s)  Controllers List: %s" % (network.name, str(expected_controllers)))

        existing_controllers = []
        for cn in ControllerNetwork.objects.all():
            slog.debug("(network.name: %s)  controllernetwork.id: %s   name: %s" % (network.name, cn.id, cn.subnet))
            slog.debug("(network.name: %s)  controllernetwork.network.id: %s" % (network.name, cn.network.id))
            if cn.network.id == network.id:
                existing_controllers.append(cn.controller)

        existing_controller_ids = [c.id for c in existing_controllers]
        slog.debug("(network.name: %s)  existing_controller_id list: %s" % (network.name, str(existing_controller_ids)))

        for expected_controller in expected_controllers:
            slog.debug("(network.name: %s)  expected_controller: %s" % (network.name, str(expected_controller))) 
            if expected_controller.id not in existing_controller_ids:
                slog.debug("(network.name: %s)  expected_controller.id: %s" % (network.name, expected_controller.id)) 
                lazy_blocked=False
                # check and see if some instance already exists
                for networkslice in network.networkslices.all():
                    slog.debug("(network.name: %s)  networkslice: %s" % (network.name, str(networkslice))) 
                    found = False
                    for instance in networkslice.slice.instances.all():
                        slog.debug("(network.name: %s)  instance.instance_name: %s" % (network.name, instance_name)) 
                        slog.debug("(network.name: %s)  instance.controller.id: %s   expected_controller.id: %s" % 
                                    (network.name, instance.node.site_deployment.controller.id, expected_controller.id)) 
                        if instance.node.site_deployment.controller.id == expected_controller.id:
                           found = True
                        slog.debug("(network.name: %s)  found: %s" % (network.name, found)) 
                    if found:
                        slog.debug("(network.name: %s) setting lazy_blocked to false because instance on controller already exists" % 
                                    network.name)
                        lazy_blocked=False

                slog.debug("(network.name: %s)  lazy_blocked: %s" % (network.name, lazy_blocked)) 

                nd = ControllerNetwork(network=network, controller=expected_controller, lazy_blocked=lazy_blocked)
                slog.debug("(network.name: %s)  create ControllerNetwork [%s] with lazy_blocked [%s]" % 
                            (network.name, nd, lazy_blocked))
                if network.subnet:
                    # XXX: Possibly unpredictable behavior if there is
                    # more than one ControllerNetwork and the subnet
                    # is specified.
                    slog.debug("(network.name: %s)  network.subnet: %s" % (network.name, network.subnet))
                    nd.subnet = network.subnet
                nd.save()
