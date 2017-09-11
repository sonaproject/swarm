#!/bin/bash

mkdir -p /root/.ssh
cp -f /opt/cord_profile/node_key  /root/.ssh/id_rsa 

while true; do
    python swarm-synchronizer.py
    # If swarm-synchronizer fails, then wait 10 seconds
    sleep 10
done
