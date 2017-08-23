#!/bin/bash

source ./config.sh

DATA=$(cat <<EOF 
{ 
    "name": "kuryr_template",
    "description": "kuryr_template for sona 08-23 09:52",
    "visibility": "private",
    "translation": "none",
    "access": null,
    "shared_network_name": "kuryr/libnetwork2:latest",
    "shared_network_id": "",
    "topology_kind": "bigswitch",
    "controller_kind": null,
    "vtn_kind": null 
}
EOF
) 

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/networktemplates/



