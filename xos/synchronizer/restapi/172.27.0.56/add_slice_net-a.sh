#!/bin/bash

source config.sh

DATA=$(cat <<EOF
{
    "name": "mysite_net-a",
    "description": "This is a slice for net-a",
    "network": "noauto",
    "site": "http://10.1.1.237/api/core/sites/1/",
    "service": "http://10.1.1.237/api/core/services/1/",
    "default_image": "http://10.1.1.237/api/core/images/1/",
    "creator": "http://10.1.1.237/api/core/users/1/"
}
EOF
)

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/slices/

