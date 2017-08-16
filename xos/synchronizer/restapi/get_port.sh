#!/bin/bash

source ./config.sh

if [[ "$#" -ne 1 ]]; then
    echo "Syntax: $0 <port_id>"
    exit -1
fi

PORT_ID=$1

curl -H "Accept: application/json; indent=4" -u $AUTH -X GET $HOST/api/core/ports/$PORT_ID/
