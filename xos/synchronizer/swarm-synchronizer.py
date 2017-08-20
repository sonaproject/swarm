#!/usr/bin/env python
import os
import argparse
import sys

sys.path.append('/opt/xos')
from xosconfig import Config

config_file = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + '/swarm_config.yaml')
# config schema path: /opt/xos/lib/xos-config/xosconfig/synchronizer-config-schema.yaml
Config.init(config_file, 'synchronizer-config-schema.yaml')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "xos.settings")

import threading 
import time 
import swarmlog as slog
import swarm_monitor

from synchronizers.new_base.modelaccessor import *
from synchronizers.new_base.backend import Backend
from synchronizers.new_base.event_loop import set_driver


def main():
    models_active = False
    wait = False

    while not models_active:
        try:
            first_controller = Controller.objects.first()
            slog.debug("one of controller set: %s" % first_controller.name) 
            first_image      = Image.objects.first()
            slog.debug("one of image set     : %s" % first_image.name) 
            models_active = True 
        except Exception,e:
            slog.info(str(e))
            slog.info('Waiting for data model to come up before starting...')
            time.sleep(3)
            wait = True

    slog.debug("Data Model is active (first_controller: %s)" % first_controller)

    if (wait):
        time.sleep(5) # Safety factor, seeing that we stumbled waiting for the data model to come up.

    # check network port on swarm cluster
    slog.debug("swarm_monitor_thread starts")
    monitor_thread = threading.Thread(target=swarm_monitor.monitor_thr, name="swarm_monitor_thread", args=(models_active,))
    monitor_thread.start() 

    backend = Backend()
    backend.run()    


if __name__ == '__main__': 
    main() 
