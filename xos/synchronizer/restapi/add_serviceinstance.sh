#!/bin/bash

source ./config.sh

DATA=$(cat <<EOF 
{ 
    "name": "testlb",
    "service_specific_id": "",
    "service_specific_attribute": "",
    "owner": "http://10.10.2.240/api/core/services/5/"
}
EOF
)

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/serviceinstances/


