from synchronizers.new_base.modelaccessor import *
from collections import defaultdict
from synchronizers.new_base.policy import Policy

class NetworkPolicy(Policy):
    model_name = "Network"

    def handle_create(self, network):
        self.logger.debug("network: %s" % str(network))
        return self.handle_update(network)

    def handle_update(self, network):
        self.logger.debug("model_policy_Network.py  network: %s  id: %s" % (str(network), network.id))

        expected_controllers =  Controller.objects.all()
        self.logger.debug("model_policy_Network.py  All Controllers: %s" % str(expected_controllers))

        existing_controllers = []
        for cn in ControllerNetwork.objects.all():
            self.logger.debug("controllernetwork.id: %s   name: %s" % (cn.id, cn.subnet))
            self.logger.debug("controllernetwork.network.id: %s" % cn.network.id)
            self.logger.debug("controllernetwork.network_id: %s" % cn.network_id)
            self.logger.debug("network.name: %s    network.id: %s" % (network.name, network.id))
            if cn.network.id == network.id:
                existing_controllers.append(cn.controller)

        existing_controller_ids = [c.id for c in existing_controllers]
        self.logger.debug("existing_controller_ids: %s" % str(existing_controller_ids))

        for expected_controller in expected_controllers:
            if expected_controller.id not in existing_controller_ids:
                lazy_blocked=True

                # check and see if some instance already exists
                for networkslice in network.networkslices.all():
                    found = False
                    for instance in networkslice.slice.instances.all():
                       if instance.node.site_deployment.controller.id == expected_controller.id:
                           found = True
                    if found:
                       self.logger.debug("network %s setting lazy_blocked to false because instance on controller already exists" % network)
                       lazy_blocked=False

                nd = ControllerNetwork(network=network, controller=expected_controller, lazy_blocked=lazy_blocked)
                self.logger.debug("network [%s] create ControllerNetwork [%s] lazy_blocked [%s]" % (network, nd, lazy_blocked))
                if network.subnet:
                    # XXX: Possibly unpredictable behavior if there is
                    # more than one ControllerNetwork and the subnet
                    # is specified.
                    nd.subnet = network.subnet
                nd.save()
