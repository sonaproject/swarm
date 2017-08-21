#!/bin/bash

source ./config.sh

# Be careful that start_ip means 'gateway ip address'
DATA=$(cat <<EOF 
{
    "name": "kuryr-net",
    "subnet": "192.168.0.0/24", 
    "start_ip": "192.168.0.1",
    "end_ip": "192.168.0.254",
    "labels": "kuryr-subnetpool",
    "permit_all_slices": true,
    "autoconnect": false,
    "template": "http://10.10.2.240/api/core/networktemplates/6/",
    "owner": "http://10.10.2.240/api/core/slices/3/"
}
EOF
) 

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/networks/


