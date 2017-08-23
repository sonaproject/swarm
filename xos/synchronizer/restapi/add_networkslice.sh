#!/bin/bash

source ./config.sh

#    "leaf_model_name": "NetworkSlice",

DATA=$(cat <<EOF 
{
    "network": "http://10.10.2.240/api/core/networks/3/",
    "slice": "http://10.10.2.240/api/core/slices/3/"
}
EOF
) 

curl -H "Accept: application/json; indent=4" -H "Content-Type: application/json" -u $AUTH -X POST -d "$DATA" $HOST/api/core/networkslices/


