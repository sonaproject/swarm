#!/bin/bash

source ./config.sh

DATA=$(cat <<EOF 
{ 
    "name": "mysite_lbaas",
    "enabled": true,
    "description": "LB slice",
    "slice_url": "",
    "max_instances": 9,
    "exposed_ports": "",
    "mount_data_sets": "/usr/local/etc/haproxy/",
    "default_isolation": "vm",
    "site": "http://10.10.2.240/api/core/sites/1/",
    "service": "http://10.10.2.240/api/core/services/2/",
    "creator": "http://10.10.2.240/api/core/users/1/",
    "default_flavor": "http://10.10.2.240/api/core/flavors/3/",
    "default_image": "http://10.10.2.240/api/core/images/1/",
    "default_node": null 
}
EOF
)

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/slices/


#    "network": null,
