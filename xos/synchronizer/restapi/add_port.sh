#!/bin/bash

source ./config.sh

## This attribute values come from "openstack port list"
DATA=$(cat <<EOF 
{ 
    "ip": "192.168.0.11",
    "port_id": "5fd7ee42-3cea-4f4c-b9d3-8e8118772130", 
    "mac": "fa:16:3e:7a:7f:72",
    "xos_created": false,
    "network": "http://10.10.2.240/api/core/networks/3/",
    "instance": "http://10.10.2.240/api/core/instances/1/" 
}
EOF
) 

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/ports/



