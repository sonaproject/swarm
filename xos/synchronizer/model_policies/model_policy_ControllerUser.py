from synchronizers.new_base.modelaccessor import *
from synchronizers.new_base.policy import Policy

class ControllerUserPolicy(Policy):
    model_name = "ControllerUser"

    def handle_create(self, controller_user):
        self.logger.info("controller_user: %s" % str(controller_user))
        return self.handle_update(controller_user)

    def handle_update(self, controller_user):
        self.logger.info("controller_user: %s" % str(controller_user))
        my_status_code = controller_user.backend_code
        try:
            his_status_code = controller_user.user.backend_code
        except:
            his_status_code = 0
 
        if (my_status_code not in [0,his_status_code]):
            controller_user.user.backend_status = controller_user.backend_status
            controller_user.user.save(update_fields = ['backend_code', 'backend_status'])
