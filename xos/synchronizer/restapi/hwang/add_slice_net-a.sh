#!/bin/bash

source .././config.sh

#    "slice_url": "",
#    "max_instances": 9,
#    "exposed_ports": "",
#    "default_isolation": "vm",
#    "default_flavor": "http://10.10.2.240/api/core/flavors/3/",
#    "default_node": null 
DATA=$(cat <<EOF 
{ 
    "name": "mysite_net-a",
    "description": "net-a",
    "network": "noauto",
    "site": "http://10.10.2.240/api/core/sites/1/",
    "service": "http://10.10.2.240/api/core/services/1/",
    "default_image": "http://10.10.2.240/api/core/images/1/",
    "creator": "http://10.10.2.240/api/core/users/1/"
}
EOF
)

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/slices/
