#!/bin/bash

source config.sh

# Be careful that start_ip means 'gateway ip address'
# Be carefule that labels means 'UUID of subnet pool'
DATA=$(cat <<EOF
{
    "name": "net-x",
    "lazy_blocked": false,
    "subnet": "192.168.24.0/24",
    "start_ip": "192.168.24.1",
    "end_ip": "192.168.24.254",
    "labels": "No subnet pool uuid",
    "permit_all_slices": true,
    "autoconnect": false,
    "template": "http://10.1.1.237/api/core/networktemplates/4/",
    "owner": "http://10.1.1.237/api/core/slices/2/"
}
EOF
)

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/networks/

