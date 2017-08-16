#!/bin/bash

source ./config.sh

if [[ "$#" -ne 1 ]]; then
    echo "Syntax: $0  <neutron_port_uuid>"
    exit -1
fi

NEUTRON_PORT_UUID=$1

curl -H "Accept: application/json; indent=4" -u $AUTH -X GET $HOST/api/core/ports/?port_id=$NEUTRON_PORT_UUID
