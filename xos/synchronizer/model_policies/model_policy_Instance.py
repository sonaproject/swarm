from synchronizers.new_base.modelaccessor import *
from synchronizers.new_base.policy import Policy

class InstancePolicy(Policy):
    model_name = "Instance"

    def handle_create(self, instance):
        self.logger.info("instance: %s" % str(instance))
        return self.handle_update(instance)

    def handle_update(self, instance):
        self.logger.info("instance: %s" % str(instance))
        networks = [ns.network for ns in NetworkSlice.objects.filter(slice_id=instance.slice.id)] 
        self.logger.info("networks: %s" % str(networks))
        controller_networks = ControllerNetwork.objects.filter(controller_id=instance.node.site_deployment.controller.id)
        self.logger.info("controller_networks: %s" % str(controller_networks))

        # a little clumsy because the API ORM doesn't support __in queries
        network_ids = [x.id for x in networks] 
        controller_networks = [x for x in controller_networks if x.network.id in network_ids]

        for cn in controller_networks: 
            if (cn.lazy_blocked):
                self.logger.info("MODEL POLICY: instance %s unblocking network %s" % (instance, cn.network))
            cn.lazy_blocked=False 
            cn.backend_register = '{}'
            cn.save()
