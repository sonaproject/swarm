#!/bin/bash

source config.sh

# Be careful that start_ip means 'gateway ip address'
# Be carefule that labels means 'UUID of subnet pool'
DATA=$(cat <<EOF
{
    "name": "net-a",
    "lazy_blocked": false,
    "subnet": "192.168.0.0/24",
    "start_ip": "192.168.0.1",
    "end_ip": "192.168.0.254",
    "labels": "7cca5644-840f-441f-922b-b40ef56d2307",
    "permit_all_slices": true,
    "autoconnect": false,
    "template": "http://10.1.1.237/api/core/networktemplates/5/",
    "owner": "http://10.1.1.237/api/core/slices/2/"
}
EOF
)

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/networks/
