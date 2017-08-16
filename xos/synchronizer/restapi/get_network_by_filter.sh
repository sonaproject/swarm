#!/bin/bash

source ./config.sh

if [[ "$#" -ne 1 ]]; then
    echo "Syntax: $0 <network_name>"
    exit -1
fi

NETWORK_NAME=$1

curl -H "Accept: application/json; indent=4" -u $AUTH -X GET $HOST/api/core/networks/?name=$NETWORK_NAME
