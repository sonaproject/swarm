#!/bin/bash 
source ./config.sh

DATA=$(cat <<EOF
{
   "site_id": 1,
   "default_image_id": 1,
   "exposed_ports": "",
   "description": "LB slice",
   "slice_url": "",
   "max_instances": 9,
   "mount_data_sets": "/usr/local/etc/haproxy/",
   "default_flavor_id": 1,
   "name": "mysite_lbaas",
   "default_isolation": "vm",
   "enabled": true,
   "service_id": 1
}
EOF
)

result_msg=`curl -X POST -u $AUTH --header 'Content-Type: application/json' --header 'Accept: text/html' -d "$DATA"  ${BASE_URL}/xosapi/v1/core/slices`
echo $result_msg | python -m json.tool
#echo $result_msg
echo ""
