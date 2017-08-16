#!/bin/bash

source ./config.sh

if [[ "$#" -ne 1 ]]; then
    echo "Syntax: $0 <my_id>"
    exit -1
fi

MY_ID=$1

curl -H "Accept: application/json; indent=4" -u $AUTH -X DELETE $HOST/api/core/networktemplates/$MY_ID/
