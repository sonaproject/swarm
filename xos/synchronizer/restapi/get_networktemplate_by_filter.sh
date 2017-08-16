#!/bin/bash

source ./config.sh

if [[ "$#" -ne 1 ]]; then
    echo "Syntax: $0 <my_name>"
    exit -1
fi

MY_NAME=$1

curl -H "Accept: application/json; indent=4" -u $AUTH -X GET $HOST/api/core/networktemplates/?name=$MY_NAME
