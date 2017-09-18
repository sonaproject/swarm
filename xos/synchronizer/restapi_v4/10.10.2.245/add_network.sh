#!/bin/bash 
source ./config.sh

# Be careful that start_ip means 'gateway ip address'
# Be careful that labels means 'UUID of subnet pool'
# "owner": "http://10.10.2.245/api/core/slices/3/"
#    "template": "http://10.10.2.245/api/core/networktemplates/6/",
#    "slices_id": 1,
#    "permit_all_slices": true,
DATA=$(cat <<EOF
{ 
    "name": "net-b",
    "subnet": "192.168.0.0/24",
    "start_ip": "192.168.0.1",
    "end_ip": "192.168.0.254",
    "labels": "6a170103-1c48-4333-a8ae-c7b55736c6d8",
    "autoconnect": false,
    "permit_all_slices": true,
    "template_id": 6,
    "owner_id": 3
}
EOF
)

curl -X POST -u $AUTH --header 'Content-Type: application/json' --header 'Accept: text/html' -d "$DATA"  ${BASE_URL}/xosapi/v1/core/networks
result_msg=`curl -X POST -u $AUTH --header 'Content-Type: application/json' --header 'Accept: text/html' -d "$DATA"  ${BASE_URL}/xosapi/v1/core/networks`
echo $result_msg | python -m json.tool
echo ""
