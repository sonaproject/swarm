#!/bin/bash

source ./config.sh

DATA=$(cat <<EOF 
{
    "name": "kuryr-net",
    "subnet": "192.168.0.0/24", 
    "start_ip": "192.168.0.3",
    "end_ip": "192.168.0.20",
    "permit_all_slices": true,
    "autoconnect": false,
    "template": "http://10.10.2.240/api/core/networktemplates/5/",
    "owner": "http://10.10.2.240/api/core/slices/3/"
}
EOF
) 

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/networks/


