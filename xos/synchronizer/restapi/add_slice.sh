#!/bin/bash

source ./config.sh

DATA=$(cat <<EOF 
{ 
    "name": "mysite_lbaas",
    "enabled": true,
    "description": "LB slice",
    "slice_url": "",
    "max_instances": 2,
    "exposed_ports": "",
    "mount_data_sets": "",
    "default_isolation": "vm",
    "site": "http://10.10.2.240/api/core/sites/1/",
    "service": null,
    "creator": "http://10.10.2.240/api/core/users/1/",
    "default_flavor": null,
    "default_image": null,
    "default_node": null 
}
EOF
)

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/slices/


#    "network": null,
