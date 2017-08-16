#!/bin/bash

source ./config.sh

if [[ "$#" -ne 1 ]]; then
    echo "Syntax: $0 <start_ip>"
    exit -1
fi

START_IP=$1

curl -H "Accept: application/json; indent=4" -u $AUTH -X GET $HOST/api/core/networks/?start_ip=$START_IP
